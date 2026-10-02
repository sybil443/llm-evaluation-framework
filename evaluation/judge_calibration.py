import math
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CalibrationExample:
    example_id: str
    expected_label: str
    judge_label: str
    expected_score: float
    judge_score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for value in (self.expected_score, self.judge_score):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("Calibration scores must be finite numbers.")
        if not self.example_id.strip():
            raise ValueError("example_id must be non-empty.")

        if not self.expected_label.strip():
            raise ValueError("expected_label must be non-empty.")

        if not self.judge_label.strip():
            raise ValueError("judge_label must be non-empty.")


@dataclass(frozen=True)
class CalibrationSummary:
    total_examples: int
    exact_label_agreement_rate: float
    within_tolerance_score_agreement_rate: float
    tolerance: float
    disagreements: list[dict[str, Any]]
    cohens_kappa: float | None = None
    mean_absolute_score_error: float | None = None
    score_pearson_correlation: float | None = None


def _validate_examples(examples: list[CalibrationExample]) -> None:
    if not examples:
        raise ValueError("At least one calibration example is required.")
    ids = [example.example_id for example in examples]
    if len(ids) != len(set(ids)):
        raise ValueError("Calibration example IDs must be unique.")


def _validate_tolerance(tolerance: float) -> None:
    if isinstance(tolerance, bool) or not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be non-negative.")


def calculate_exact_label_agreement(examples: list[CalibrationExample]) -> float:
    """
    Calculate the percentage of examples where the judge label exactly
    matches the expected label.
    """
    _validate_examples(examples)

    matching_count = sum(
        example.expected_label == example.judge_label
        for example in examples
    )

    return matching_count / len(examples)


def calculate_within_tolerance_score_agreement(
    examples: list[CalibrationExample],
    tolerance: float,
) -> float:
    """
    Calculate the percentage of examples where the judge score is within
    the allowed tolerance of the expected score.
    """
    _validate_examples(examples)
    _validate_tolerance(tolerance)

    within_tolerance_count = sum(
        abs(example.expected_score - example.judge_score) <= tolerance
        for example in examples
    )

    return within_tolerance_count / len(examples)


def find_disagreements(
    examples: list[CalibrationExample],
    tolerance: float,
) -> list[dict[str, Any]]:
    """
    Return examples where the judge disagrees with the expected label,
    the expected score, or both.
    """
    _validate_examples(examples)
    _validate_tolerance(tolerance)

    disagreements: list[dict[str, Any]] = []

    for example in examples:
        label_mismatch = example.expected_label != example.judge_label
        score_difference = abs(example.expected_score - example.judge_score)
        score_outside_tolerance = score_difference > tolerance

        if not label_mismatch and not score_outside_tolerance:
            continue

        if label_mismatch and score_outside_tolerance:
            reason = "label_mismatch_and_score_outside_tolerance"
        elif label_mismatch:
            reason = "label_mismatch"
        else:
            reason = "score_outside_tolerance"

        disagreements.append(
            {
                "example_id": example.example_id,
                "expected_label": example.expected_label,
                "judge_label": example.judge_label,
                "expected_score": example.expected_score,
                "judge_score": example.judge_score,
                "score_difference": score_difference,
                "reason": reason,
                "metadata": example.metadata,
            }
        )

    return disagreements


def _label_counts(examples: list[CalibrationExample], attr: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for example in examples:
        label = getattr(example, attr)
        counts[label] = counts.get(label, 0) + 1
    return counts


def calculate_cohens_kappa(examples: list[CalibrationExample]) -> float | None:
    """
    Cohen's kappa between expected_label and judge_label: exact agreement
    corrected for the agreement expected by chance given each side's own
    label distribution. 0 means agreement no better than chance; 1 means
    perfect agreement; negative values mean worse than chance.

    Returns None when chance agreement is already 1.0 (every example
    shares the same single label on both sides), where kappa's
    denominator is zero and the statistic is undefined rather than any
    specific number.
    """
    _validate_examples(examples)
    n = len(examples)
    observed = calculate_exact_label_agreement(examples)
    expected_counts = _label_counts(examples, "expected_label")
    judge_counts = _label_counts(examples, "judge_label")
    labels = set(expected_counts) | set(judge_counts)
    chance = sum((expected_counts.get(label, 0) / n) * (judge_counts.get(label, 0) / n)
                 for label in labels)
    if math.isclose(chance, 1.0):
        return None
    return (observed - chance) / (1 - chance)


def calculate_mean_absolute_score_error(examples: list[CalibrationExample]) -> float:
    """Mean of |expected_score - judge_score| across all examples."""
    _validate_examples(examples)
    return sum(abs(example.expected_score - example.judge_score) for example in examples) / len(examples)


def calculate_score_pearson_correlation(examples: list[CalibrationExample]) -> float | None:
    """
    Pearson correlation between expected_score and judge_score.

    Returns None when fewer than two examples are given, or when either
    side has zero variance (a constant expected or judge score makes the
    correlation coefficient undefined, not zero).
    """
    _validate_examples(examples)
    n = len(examples)
    if n < 2:
        return None
    expected = [example.expected_score for example in examples]
    judged = [example.judge_score for example in examples]
    mean_expected = sum(expected) / n
    mean_judged = sum(judged) / n
    covariance = sum((x - mean_expected) * (y - mean_judged) for x, y in zip(expected, judged))
    variance_expected = sum((x - mean_expected) ** 2 for x in expected)
    variance_judged = sum((y - mean_judged) ** 2 for y in judged)
    if variance_expected == 0 or variance_judged == 0:
        return None
    return covariance / math.sqrt(variance_expected * variance_judged)


def summarize_calibration_results(
    examples: list[CalibrationExample],
    tolerance: float = 0.5,
) -> CalibrationSummary:
    """
    Produce a calibration summary with label agreement, score agreement,
    and disagreement records.
    """
    _validate_examples(examples)
    _validate_tolerance(tolerance)

    return CalibrationSummary(
        total_examples=len(examples),
        exact_label_agreement_rate=calculate_exact_label_agreement(examples),
        within_tolerance_score_agreement_rate=(
            calculate_within_tolerance_score_agreement(
                examples=examples,
                tolerance=tolerance,
            )
        ),
        tolerance=tolerance,
        disagreements=find_disagreements(
            examples=examples,
            tolerance=tolerance,
        ),
        cohens_kappa=calculate_cohens_kappa(examples),
        mean_absolute_score_error=calculate_mean_absolute_score_error(examples),
        score_pearson_correlation=calculate_score_pearson_correlation(examples),
    )


def judge_passes_calibration(
    summary: CalibrationSummary,
    min_label_agreement_rate: float = 0.8,
    min_score_agreement_rate: float = 0.8,
    min_kappa: float | None = None,
) -> bool:
    """
    Return whether the judge passes a simple calibration gate.

    This is intentionally a lightweight first-pass rule. Production
    thresholds should depend on task risk and review requirements.

    `min_kappa`, if given, additionally requires `summary.cohens_kappa` to
    be at least that value. It is optional and off by default because raw
    label-agreement rate can look good on an imbalanced label set even
    when agreement is barely better than chance; kappa is the corrected
    check, for callers who want it enforced. It raises if `summary` has
    no kappa value to check (see calculate_cohens_kappa's None case).
    """
    if not 0 <= min_label_agreement_rate <= 1:
        raise ValueError("min_label_agreement_rate must be between 0 and 1.")

    if not 0 <= min_score_agreement_rate <= 1:
        raise ValueError("min_score_agreement_rate must be between 0 and 1.")

    if min_kappa is not None:
        if not -1 <= min_kappa <= 1:
            raise ValueError("min_kappa must be between -1 and 1.")
        if summary.cohens_kappa is None:
            raise ValueError("Cannot enforce min_kappa: summary has no cohens_kappa value.")
        if summary.cohens_kappa < min_kappa:
            return False

    return (
        summary.exact_label_agreement_rate >= min_label_agreement_rate
        and summary.within_tolerance_score_agreement_rate >= min_score_agreement_rate
    )

