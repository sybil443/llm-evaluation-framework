import pytest

from evaluation.significance import (
    SignificanceVerdict,
    classify_bootstrap_summary,
    classify_many,
    classify_significance,
)


def test_significant_and_practical_when_ci_excludes_zero_and_effect_is_large() -> None:
    result = classify_significance(0.2, 0.05, 0.35, minimum_effect=0.1)

    assert result.verdict == SignificanceVerdict.SIGNIFICANT_AND_PRACTICAL
    assert result.is_statistically_significant is True
    assert result.is_practically_significant is True
    assert result.direction == "positive"


def test_significant_not_practical_when_ci_excludes_zero_but_effect_is_small() -> None:
    result = classify_significance(0.02, 0.01, 0.03, minimum_effect=0.1)

    assert result.verdict == SignificanceVerdict.SIGNIFICANT_NOT_PRACTICAL
    assert result.is_statistically_significant is True
    assert result.is_practically_significant is False


def test_practical_not_significant_when_ci_includes_zero_but_effect_is_large() -> None:
    result = classify_significance(0.2, -0.05, 0.4, minimum_effect=0.1)

    assert result.verdict == SignificanceVerdict.PRACTICAL_NOT_SIGNIFICANT
    assert result.is_statistically_significant is False
    assert result.is_practically_significant is True


def test_inconclusive_when_ci_includes_zero_and_effect_is_small() -> None:
    result = classify_significance(0.02, -0.05, 0.09, minimum_effect=0.1)

    assert result.verdict == SignificanceVerdict.INCONCLUSIVE
    assert result.is_statistically_significant is False
    assert result.is_practically_significant is False


def test_negative_direction_is_reported() -> None:
    result = classify_significance(-0.2, -0.35, -0.05, minimum_effect=0.1)

    assert result.direction == "negative"
    assert result.verdict == SignificanceVerdict.SIGNIFICANT_AND_PRACTICAL


def test_zero_point_estimate_has_zero_direction() -> None:
    result = classify_significance(0.0, -0.1, 0.1)

    assert result.direction == "zero"


def test_default_minimum_effect_is_zero_so_significance_alone_is_practical() -> None:
    result = classify_significance(0.001, 0.0005, 0.0015)

    assert result.is_practically_significant is True
    assert result.verdict == SignificanceVerdict.SIGNIFICANT_AND_PRACTICAL


def test_rejects_ci_lower_greater_than_ci_upper() -> None:
    with pytest.raises(ValueError, match="ci_lower"):
        classify_significance(0.1, 0.5, 0.2)


def test_rejects_non_finite_inputs() -> None:
    with pytest.raises(ValueError, match="finite"):
        classify_significance(float("nan"), 0.0, 0.1)


def test_rejects_negative_minimum_effect() -> None:
    with pytest.raises(ValueError, match="minimum_effect"):
        classify_significance(0.1, 0.0, 0.2, minimum_effect=-0.01)


def test_classify_bootstrap_summary_reads_mean_and_ci() -> None:
    summary = dict(mean=0.3, ci_lower=0.1, ci_upper=0.5)

    result = classify_bootstrap_summary(summary, minimum_effect=0.1)

    assert result.point_estimate == 0.3
    assert result.verdict == SignificanceVerdict.SIGNIFICANT_AND_PRACTICAL


def test_classify_bootstrap_summary_prefers_mean_difference_when_present() -> None:
    summary = dict(mean_difference=0.3, mean_a=0.1, mean_b=0.4, ci_lower=0.1, ci_upper=0.5)

    result = classify_bootstrap_summary(summary)

    assert result.point_estimate == 0.3


def test_classify_bootstrap_summary_rejects_missing_mean_fields() -> None:
    with pytest.raises(ValueError, match="mean"):
        classify_bootstrap_summary(dict(ci_lower=0.1, ci_upper=0.2))


def test_classify_bootstrap_summary_rejects_missing_ci_fields() -> None:
    with pytest.raises(ValueError, match="ci_lower"):
        classify_bootstrap_summary(dict(mean=0.1))


def test_classify_many_returns_one_result_per_key() -> None:
    summaries = dict(
        metric_a=dict(mean=0.2, ci_lower=0.1, ci_upper=0.3),
        metric_b=dict(mean=0.0, ci_lower=-0.1, ci_upper=0.1),
    )

    results = classify_many(summaries, minimum_effect=0.05)

    assert set(results) == {"metric_a", "metric_b"}
    assert results["metric_a"].verdict == SignificanceVerdict.SIGNIFICANT_AND_PRACTICAL
    assert results["metric_b"].verdict == SignificanceVerdict.INCONCLUSIVE


def test_classify_many_rejects_empty_dict() -> None:
    with pytest.raises(ValueError, match="not be empty"):
        classify_many({})
