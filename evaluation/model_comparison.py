"""Paired baseline-vs-challenger model comparison and latency trade-offs.

Wraps the canonical paired bootstrap in evaluation/statistics.py into a
report-ready comparison, and adds latency/throughput helpers for choosing
a batch size under a latency budget.
"""
from dataclasses import dataclass

from evaluation.statistics import bootstrap_summary, finite_values, paired_summary

@dataclass(frozen=True)
class PairedComparisonResult:
    mean_model_a: float
    mean_model_b: float
    mean_difference: float
    ci_lower: float
    ci_upper: float
    positive_resample_fraction: float
    n_samples: int
    n_bootstrap: int
    seed: int
    confidence_level: float = 0.95


@dataclass(frozen=True)
class LatencyProfile:
    batch_size: int
    latency_seconds: float
    throughput_per_second: float

def paired_score_differences(
    model_a_scores: list[float],
    model_b_scores: list[float],
) -> list[float]:
    """
    Calculate paired score differences as model_b_score - model_a_score.
    """
    if len(model_a_scores) != len(model_b_scores):
        raise ValueError("Model score lists must have the same length.")

    if not model_a_scores:
        raise ValueError("At least one paired score is required.")

    model_a_scores = finite_values(model_a_scores, "model_a_scores")
    model_b_scores = finite_values(model_b_scores, "model_b_scores")
    return [
        model_b_score - model_a_score
        for model_a_score, model_b_score in zip(model_a_scores, model_b_scores)
    ]


def bootstrap_confidence_interval_for_mean(values, *, n_bootstrap=10_000,
                                           confidence_level=0.95, seed=42):
    result = bootstrap_summary(values, n_bootstrap, confidence_level, seed)
    return result["ci_lower"], result["ci_upper"]


def compare_paired_model_scores(model_a_scores, model_b_scores, *,
                                n_bootstrap=10_000, confidence_level=0.95, seed=42):
    result = paired_summary(model_a_scores, model_b_scores, n_bootstrap, confidence_level, seed)
    return PairedComparisonResult(
        mean_model_a=result["mean_a"], mean_model_b=result["mean_b"],
        mean_difference=result["mean_difference"], ci_lower=result["ci_lower"],
        ci_upper=result["ci_upper"], positive_resample_fraction=result["positive_resample_fraction"],
        n_samples=result["n_pairs"], n_bootstrap=n_bootstrap, seed=seed,
        confidence_level=confidence_level,
    )


def calculate_throughput(
    *,
    batch_size: int,
    latency_seconds: float,
) -> float:
    """
    Calculate examples processed per second.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be positive.")

    if latency_seconds <= 0:
        raise ValueError("latency_seconds must be positive.")

    return batch_size / latency_seconds


def build_latency_profiles(
    latency_by_batch_size: dict[int, float],
) -> list[LatencyProfile]:
    """
    Convert raw batch-size latency results into latency/throughput profiles.
    """
    if not latency_by_batch_size:
        raise ValueError("At least one latency result is required.")

    profiles = [
        LatencyProfile(
            batch_size=batch_size,
            latency_seconds=latency_seconds,
            throughput_per_second=calculate_throughput(
                batch_size=batch_size,
                latency_seconds=latency_seconds,
            ),
        )
        for batch_size, latency_seconds in latency_by_batch_size.items()
    ]

    return sorted(profiles, key=lambda profile: profile.batch_size)


def recommend_batch_size(
    latency_by_batch_size: dict[int, float],
    *,
    max_acceptable_latency_seconds: float,
) -> LatencyProfile:
    """
    Recommend the highest-throughput batch size that stays within the
    maximum acceptable latency threshold.
    """
    if max_acceptable_latency_seconds <= 0:
        raise ValueError("max_acceptable_latency_seconds must be positive.")

    profiles = build_latency_profiles(latency_by_batch_size)

    eligible_profiles = [
        profile
        for profile in profiles
        if profile.latency_seconds <= max_acceptable_latency_seconds
    ]

    if not eligible_profiles:
        raise ValueError("No batch size meets the latency requirement.")

    return max(
        eligible_profiles,
        key=lambda profile: profile.throughput_per_second,
    )


def build_evaluation_report_summary(
    *,
    model_a_name: str,
    model_b_name: str,
    model_a_scores: list[float],
    model_b_scores: list[float],
    latency_by_batch_size: dict[int, float] | None = None,
    max_acceptable_latency_seconds: float | None = None,
    n_bootstrap: int = 10_000,
    seed: int = 42,
) -> dict:
    """
    Build a report-ready summary that combines model-quality comparison
    with optional latency/throughput analysis.
    """
    comparison = compare_paired_model_scores(
        model_a_scores,
        model_b_scores,
        n_bootstrap=n_bootstrap,
        seed=seed,
    )

    summary = {
        "model_a_name": model_a_name,
        "model_b_name": model_b_name,
        "mean_model_a": comparison.mean_model_a,
        "mean_model_b": comparison.mean_model_b,
        "mean_difference": comparison.mean_difference,
        "ci_lower": comparison.ci_lower,
        "ci_upper": comparison.ci_upper,
        "positive_resample_fraction": comparison.positive_resample_fraction,
        "confidence_level": comparison.confidence_level,
        "n_samples": comparison.n_samples,
        "n_bootstrap": comparison.n_bootstrap,
        "seed": comparison.seed,
        "recommendation": interpret_paired_comparison(comparison),
    }

    if latency_by_batch_size is not None:
        summary["latency_profiles"] = [
            {
                "batch_size": profile.batch_size,
                "latency_seconds": profile.latency_seconds,
                "throughput_per_second": profile.throughput_per_second,
            }
            for profile in build_latency_profiles(latency_by_batch_size)
        ]

    if (
        latency_by_batch_size is not None
        and max_acceptable_latency_seconds is not None
    ):
        recommended_profile = recommend_batch_size(
            latency_by_batch_size,
            max_acceptable_latency_seconds=max_acceptable_latency_seconds,
        )
        summary["recommended_batch_size"] = recommended_profile.batch_size
        summary["recommended_batch_size_latency_seconds"] = (
            recommended_profile.latency_seconds
        )
        summary["recommended_batch_size_throughput_per_second"] = (
            recommended_profile.throughput_per_second
        )

    return summary


def interpret_paired_comparison(result: PairedComparisonResult) -> str:
    """
    Interpret paired comparison results using the confidence interval.
    """
    if result.ci_lower > 0:
        return (
            "Model B shows a positive improvement with the confidence interval "
            "entirely above zero."
        )

    if result.ci_upper < 0:
        return (
            "Model B appears worse than Model A because the confidence interval "
            "is entirely below zero."
        )

    return (
        "The result is inconclusive because the confidence interval includes zero."
    )