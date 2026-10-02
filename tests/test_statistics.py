"""
Direct unit tests for evaluation/statistics.py — the one canonical
bootstrap implementation the rest of the repo uses (evaluation/pipeline.py,
evaluation/retrieval_metrics.py, evaluation/significance.py, and others,
via bootstrap_summary/paired_summary).
"""
import pytest

from evaluation.statistics import bootstrap_distribution, bootstrap_summary, finite_values, paired_summary


# --- finite_values ----------------------------------------------------------


def test_finite_values_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        finite_values([])


@pytest.mark.parametrize("values", [[float("nan")], [float("inf")], [True], ["0.5"]])
def test_finite_values_rejects_non_finite_or_non_numeric_or_boolean(values) -> None:
    with pytest.raises(ValueError, match="finite numbers"):
        finite_values(values)


def test_finite_values_converts_ints_to_floats() -> None:
    assert finite_values([1, 2, 3]) == [1.0, 2.0, 3.0]


# --- bootstrap_distribution ---------------------------------------------


def test_bootstrap_distribution_returns_one_mean_per_resample() -> None:
    result = bootstrap_distribution([1.0, 2.0, 3.0], n_resamples=50, seed=42)

    assert len(result) == 50


def test_bootstrap_distribution_rejects_out_of_range_resample_count() -> None:
    with pytest.raises(ValueError, match="n_resamples"):
        bootstrap_distribution([1.0, 2.0], n_resamples=0)
    with pytest.raises(ValueError, match="n_resamples"):
        bootstrap_distribution([1.0, 2.0], n_resamples=100_001)


def test_bootstrap_distribution_rejects_non_integer_resample_count() -> None:
    with pytest.raises(ValueError, match="n_resamples"):
        bootstrap_distribution([1.0, 2.0], n_resamples=1.5)
    with pytest.raises(ValueError, match="n_resamples"):
        bootstrap_distribution([1.0, 2.0], n_resamples=True)


def test_bootstrap_distribution_rejects_negative_seed() -> None:
    with pytest.raises(ValueError, match="seed"):
        bootstrap_distribution([1.0, 2.0], seed=-1)


def test_bootstrap_distribution_accepts_none_seed() -> None:
    result = bootstrap_distribution([1.0, 2.0, 3.0], n_resamples=10, seed=None)

    assert len(result) == 10


# --- bootstrap_summary ----------------------------------------------------


def test_bootstrap_summary_returns_expected_keys() -> None:
    result = bootstrap_summary([1.0, 2.0, 3.0], n_resamples=100, seed=42)

    assert set(result) == {
        "mean", "ci_lower", "ci_upper", "confidence_level",
        "positive_resample_fraction", "n", "n_resamples", "seed",
    }


def test_bootstrap_summary_constant_sample_has_exact_bounds() -> None:
    result = bootstrap_summary([2.0] * 8, n_resamples=100, seed=42)

    assert result["mean"] == 2.0
    assert result["ci_lower"] == 2.0
    assert result["ci_upper"] == 2.0
    assert result["n"] == 8


def test_bootstrap_summary_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        bootstrap_summary([])


def test_bootstrap_summary_rejects_invalid_confidence_level() -> None:
    for confidence_level in (0.0, 1.0, -0.01, 1.01):
        with pytest.raises(ValueError, match="confidence_level"):
            bootstrap_summary([1.0, 2.0], confidence_level=confidence_level)


def test_bootstrap_summary_rejects_boolean_confidence_level() -> None:
    with pytest.raises(ValueError, match="confidence_level"):
        bootstrap_summary([1.0, 2.0], confidence_level=True)


def test_bootstrap_summary_is_reproducible_with_the_same_seed() -> None:
    values = [0.72, 0.81, 0.77, 0.69, 0.85]

    first = bootstrap_summary(values, n_resamples=1000, confidence_level=0.95, seed=42)
    second = bootstrap_summary(values, n_resamples=1000, confidence_level=0.95, seed=42)

    assert first == second


def test_bootstrap_summary_wider_confidence_level_widens_interval() -> None:
    low = bootstrap_summary([0, 0.1, 0.3, 1, 2], n_resamples=1000, confidence_level=0.8)
    high = bootstrap_summary([0, 0.1, 0.3, 1, 2], n_resamples=1000, confidence_level=0.99)

    assert high["ci_lower"] <= low["ci_lower"]
    assert high["ci_upper"] >= low["ci_upper"]
    assert high["confidence_level"] == 0.99


# --- paired_summary --------------------------------------------------------


def test_paired_summary_rejects_unequal_lengths() -> None:
    with pytest.raises(ValueError, match="equal length"):
        paired_summary([1.0, 2.0], [1.0])


def test_paired_summary_rejects_empty_lists() -> None:
    with pytest.raises(ValueError, match="At least one score pair"):
        paired_summary([], [])


def test_paired_summary_rejects_non_finite_scores() -> None:
    with pytest.raises(ValueError, match="scores_a"):
        paired_summary([float("nan")], [1.0])
    with pytest.raises(ValueError, match="scores_b"):
        paired_summary([1.0], [float("inf")])


def test_paired_summary_is_reproducible_with_the_same_seed() -> None:
    scores_a = [0.62, 0.71, 0.58, 0.80, 0.66]
    scores_b = [0.68, 0.74, 0.63, 0.82, 0.70]

    first = paired_summary(scores_a, scores_b, n_resamples=1000, seed=42)
    second = paired_summary(scores_a, scores_b, n_resamples=1000, seed=42)

    assert first == second


def test_paired_summary_mean_difference_is_zero_for_identical_scores() -> None:
    scores = [0.55, 0.72, 0.81, 0.64]

    result = paired_summary(scores, scores, n_resamples=1000, seed=42)

    assert result["mean_difference"] == pytest.approx(0.0)
    assert result["ci_lower"] <= 0.0
    assert result["ci_upper"] >= 0.0


def test_paired_summary_is_positive_when_b_is_clearly_better() -> None:
    scores_a = [0.40, 0.45, 0.42, 0.38, 0.41]
    scores_b = [0.85, 0.88, 0.90, 0.87, 0.89]

    result = paired_summary(scores_a, scores_b, n_resamples=1000, seed=42)

    assert result["mean_difference"] > 0.0
    assert result["positive_resample_fraction"] > 0.9


def test_paired_summary_constant_difference_has_exact_interval() -> None:
    result = paired_summary([1, 2, 3], [3, 4, 5], n_resamples=100)

    assert result["mean_difference"] == 2
    assert result["ci_lower"] == result["ci_upper"] == 2
    assert result["positive_resample_fraction"] == 1


def test_paired_summary_returns_expected_keys() -> None:
    result = paired_summary([1.0, 2.0], [2.0, 3.0], n_resamples=100)

    assert set(result) == {
        "mean_difference", "ci_lower", "ci_upper", "confidence_level",
        "positive_resample_fraction", "n_pairs", "n_resamples", "seed",
        "mean_a", "mean_b",
    }
