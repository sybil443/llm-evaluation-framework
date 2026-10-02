import pytest

from evaluation.model_comparison import (
    bootstrap_confidence_interval_for_mean,
    build_evaluation_report_summary,
    build_latency_profiles,
    calculate_throughput,
    compare_paired_model_scores,
    interpret_paired_comparison,
    paired_score_differences,
    recommend_batch_size,
)

def test_paired_score_differences_calculates_model_b_minus_model_a() -> None:
    differences = paired_score_differences(
        model_a_scores=[0.0, 1.0, 0.0],
        model_b_scores=[1.0, 1.0, 0.0],
    )

    assert differences == [1.0, 0.0, 0.0]


def test_bootstrap_confidence_interval_for_mean_is_deterministic() -> None:
    ci_lower, ci_upper = bootstrap_confidence_interval_for_mean(
        [1.0, 0.0, 1.0, 1.0],
        n_bootstrap=500,
        seed=123,
    )

    assert 0.0 <= ci_lower <= ci_upper <= 1.0


def test_compare_paired_model_scores_returns_report_ready_result() -> None:
    result = compare_paired_model_scores(
        model_a_scores=[0.0, 1.0, 0.0, 1.0],
        model_b_scores=[1.0, 1.0, 1.0, 1.0],
        n_bootstrap=500,
        seed=123,
    )

    assert result.mean_model_a == pytest.approx(0.5)
    assert result.mean_model_b == pytest.approx(1.0)
    assert result.mean_difference == pytest.approx(0.5)
    assert result.n_samples == 4
    assert result.n_bootstrap == 500
    assert result.seed == 123
    assert result.positive_resample_fraction > 0.0


def test_interpret_paired_comparison_flags_positive_result() -> None:
    result = compare_paired_model_scores(
        model_a_scores=[0.0, 0.0, 0.0, 0.0],
        model_b_scores=[1.0, 1.0, 1.0, 1.0],
        n_bootstrap=500,
        seed=123,
    )

    assert interpret_paired_comparison(result).startswith("Model B shows")


def test_calculate_throughput_returns_examples_per_second() -> None:
    throughput = calculate_throughput(
        batch_size=8,
        latency_seconds=2.0,
    )

    assert throughput == pytest.approx(4.0)


def test_calculate_throughput_rejects_invalid_latency() -> None:
    with pytest.raises(ValueError, match="latency_seconds"):
        calculate_throughput(batch_size=8, latency_seconds=0.0)


def test_build_latency_profiles_sorts_by_batch_size() -> None:
    profiles = build_latency_profiles(
        {
            8: 2.0,
            1: 0.5,
            4: 1.0,
        }
    )

    assert [profile.batch_size for profile in profiles] == [1, 4, 8]
    assert profiles[0].throughput_per_second == pytest.approx(2.0)
    assert profiles[1].throughput_per_second == pytest.approx(4.0)
    assert profiles[2].throughput_per_second == pytest.approx(4.0)


def test_recommend_batch_size_chooses_highest_throughput_under_latency_limit() -> None:
    recommendation = recommend_batch_size(
        {
            1: 0.4,
            4: 0.9,
            8: 1.8,
            16: 4.0,
        },
        max_acceptable_latency_seconds=2.0,
    )

    assert recommendation.batch_size == 4


def test_recommend_batch_size_rejects_when_no_batch_meets_latency_limit() -> None:
    with pytest.raises(ValueError, match="No batch size"):
        recommend_batch_size(
            {
                1: 0.4,
                4: 0.9,
            },
            max_acceptable_latency_seconds=0.1,
        )


def test_build_evaluation_report_summary_combines_quality_and_latency() -> None:
    summary = build_evaluation_report_summary(
        model_a_name="model-a",
        model_b_name="model-b",
        model_a_scores=[0.0, 1.0, 0.0, 1.0],
        model_b_scores=[1.0, 1.0, 1.0, 1.0],
        latency_by_batch_size={
            1: 0.4,
            4: 0.9,
            8: 1.8,
        },
        max_acceptable_latency_seconds=2.0,
        n_bootstrap=500,
        seed=123,
    )

    assert summary["model_a_name"] == "model-a"
    assert summary["model_b_name"] == "model-b"
    assert summary["mean_model_a"] == pytest.approx(0.5)
    assert summary["mean_model_b"] == pytest.approx(1.0)
    assert summary["recommended_batch_size"] == 4
    assert len(summary["latency_profiles"]) == 3