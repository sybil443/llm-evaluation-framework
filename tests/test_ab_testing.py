import pytest

from evaluation.ab_testing import (
    confidence_interval_for_rate_difference,
    interpret_ab_test_result,
    should_ship_treatment,
    two_proportion_z_test,
)

def test_two_proportion_z_test_detects_significant_treatment_lift() -> None:
    result = two_proportion_z_test(
        control_successes=120,
        control_total=1000,
        treatment_successes=170,
        treatment_total=1000,
    )

    assert result.control_rate == pytest.approx(0.12)
    assert result.treatment_rate == pytest.approx(0.17)
    assert result.absolute_lift == pytest.approx(0.05)
    assert result.relative_lift == pytest.approx(0.4166666667)
    assert result.p_value < 0.05
    assert result.ci_lower > 0
    assert result.ci_upper > 0


def test_two_proportion_z_test_returns_non_significant_result_for_small_lift() -> None:
    result = two_proportion_z_test(
        control_successes=120,
        control_total=1000,
        treatment_successes=125,
        treatment_total=1000,
    )

    assert result.absolute_lift == pytest.approx(0.005)
    assert result.p_value >= 0.05
    assert result.ci_lower < 0
    assert result.ci_upper > 0


def test_confidence_interval_for_rate_difference_returns_expected_range() -> None:
    ci_lower, ci_upper = confidence_interval_for_rate_difference(
        control_successes=120,
        control_total=1000,
        treatment_successes=170,
        treatment_total=1000,
    )

    assert ci_lower == pytest.approx(0.0183, abs=0.001)
    assert ci_upper == pytest.approx(0.0817, abs=0.001)


def test_should_ship_treatment_returns_true_for_significant_practical_lift() -> None:
    result = two_proportion_z_test(
        control_successes=120,
        control_total=1000,
        treatment_successes=170,
        treatment_total=1000,
    )

    assert should_ship_treatment(result, minimum_effect_size=0.02)


def test_should_ship_treatment_returns_false_for_non_significant_lift() -> None:
    result = two_proportion_z_test(
        control_successes=120,
        control_total=1000,
        treatment_successes=125,
        treatment_total=1000,
    )

    assert not should_ship_treatment(result, minimum_effect_size=0.02)


def test_should_ship_treatment_returns_false_when_effect_size_is_too_small() -> None:
    result = two_proportion_z_test(
        control_successes=1200,
        control_total=10000,
        treatment_successes=1250,
        treatment_total=10000,
    )

    assert not should_ship_treatment(result, minimum_effect_size=0.01)


def test_interpret_ab_test_result_recommends_shipping_when_criteria_are_met() -> None:
    result = two_proportion_z_test(
        control_successes=120,
        control_total=1000,
        treatment_successes=170,
        treatment_total=1000,
    )

    interpretation = interpret_ab_test_result(
        result,
        minimum_effect_size=0.02,
    )

    assert interpretation.startswith("Ship treatment")


def test_interpret_ab_test_result_recommends_hold_for_non_significant_result() -> None:
    result = two_proportion_z_test(
        control_successes=120,
        control_total=1000,
        treatment_successes=125,
        treatment_total=1000,
    )

    interpretation = interpret_ab_test_result(
        result,
        minimum_effect_size=0.02,
    )

    assert interpretation.startswith("Hold")


def test_two_proportion_z_test_rejects_invalid_counts() -> None:
    with pytest.raises(ValueError, match="cannot exceed"):
        two_proportion_z_test(
            control_successes=11,
            control_total=10,
            treatment_successes=5,
            treatment_total=10,
        )


def test_two_proportion_z_test_rejects_invalid_alternative() -> None:
    with pytest.raises(ValueError, match="alternative"):
        two_proportion_z_test(
            control_successes=5,
            control_total=10,
            treatment_successes=6,
            treatment_total=10,
            alternative="invalid",
        )


def test_confidence_interval_rejects_invalid_alpha() -> None:
    with pytest.raises(ValueError, match="alpha must be between"):
        confidence_interval_for_rate_difference(
            control_successes=120,
            control_total=1000,
            treatment_successes=170,
            treatment_total=1000,
            alpha=-0.03,
        )