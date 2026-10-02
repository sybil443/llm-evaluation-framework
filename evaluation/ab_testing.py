"""Independent-group A/B testing for binary outcomes.

Two-proportion z-test, a normal-approximation interval for the rate
difference, and a ship/hold rule that requires both statistical and
practical significance. For independent groups only; same-prompt paired
scores belong in evaluation/model_comparison.py.
"""
from dataclasses import dataclass
from statistics import NormalDist
import math

@dataclass(frozen=True)
class TwoProportionTestResult:
    control_rate: float
    treatment_rate: float
    absolute_lift: float
    relative_lift: float
    z_statistic: float
    p_value: float
    ci_lower: float
    ci_upper: float
    alpha: float


def two_proportion_z_test(
    *,
    control_successes: int,
    control_total: int,
    treatment_successes: int,
    treatment_total: int,
    alpha: float = 0.05,
    alternative: str = "two-sided",
) -> TwoProportionTestResult:
    """
    Compare two binary conversion rates using a two-proportion z-test.

    This is useful for A/B testing LLM prompts, model variants, or product
    changes when the outcome is binary, such as converted/not converted,
    accepted/rejected, or resolved/not resolved.
    """
    _validate_proportion_inputs(
        successes=control_successes,
        total=control_total,
        label="control",
    )
    _validate_proportion_inputs(
        successes=treatment_successes,
        total=treatment_total,
        label="treatment",
    )

    if alternative not in {"two-sided", "greater", "less"}:
        raise ValueError("alternative must be 'two-sided', 'greater', or 'less'.")

    # Independent Bernoulli groups; require adequate pooled expected cells.
    pooled = (control_successes + treatment_successes) / (control_total + treatment_total)
    cells = [control_total * pooled, control_total * (1 - pooled),
             treatment_total * pooled, treatment_total * (1 - pooled)]
    if min(cells) < 5:
        raise ValueError("Normal approximation requires each pooled expected cell >= 5.")
    control_rate = control_successes / control_total
    treatment_rate = treatment_successes / treatment_total
    absolute_lift = treatment_rate - control_rate
    relative_lift = (
        absolute_lift / control_rate
        if control_rate != 0
        else math.inf
    )

    pooled_rate = (
        control_successes + treatment_successes
    ) / (
        control_total + treatment_total
    )

    pooled_standard_error = math.sqrt(
        pooled_rate
        * (1 - pooled_rate)
        * ((1 / control_total) + (1 / treatment_total))
    )

    if pooled_standard_error == 0:
        z_statistic = 0.0
        p_value = 1.0
    else:
        z_statistic = absolute_lift / pooled_standard_error
        p_value = _p_value_from_z(z_statistic, alternative=alternative)

    ci_lower, ci_upper = confidence_interval_for_rate_difference(
        control_successes=control_successes,
        control_total=control_total,
        treatment_successes=treatment_successes,
        treatment_total=treatment_total,
        alpha=alpha,
    )

    return TwoProportionTestResult(
        control_rate=control_rate,
        treatment_rate=treatment_rate,
        absolute_lift=absolute_lift,
        relative_lift=relative_lift,
        z_statistic=z_statistic,
        p_value=p_value,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        alpha=alpha,
    )


def confidence_interval_for_rate_difference(
    *,
    control_successes: int,
    control_total: int,
    treatment_successes: int,
    treatment_total: int,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """
    Compute a normal-approximation confidence interval for treatment-control lift.
    """
    _validate_proportion_inputs(
        successes=control_successes,
        total=control_total,
        label="control",
    )
    _validate_proportion_inputs(
        successes=treatment_successes,
        total=treatment_total,
        label="treatment",
    )

    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1.")

    if min(control_successes, control_total - control_successes,
           treatment_successes, treatment_total - treatment_successes) < 5:
        raise ValueError("Normal interval requires at least 5 successes and failures per group.")

    control_rate = control_successes / control_total
    treatment_rate = treatment_successes / treatment_total
    difference = treatment_rate - control_rate

    standard_error = math.sqrt(
        (control_rate * (1 - control_rate) / control_total)
        + (treatment_rate * (1 - treatment_rate) / treatment_total)
    )

    z_critical = _z_critical_for_alpha(alpha)
    margin_of_error = z_critical * standard_error

    return difference - margin_of_error, difference + margin_of_error


def should_ship_treatment(
    result: TwoProportionTestResult,
    *,
    minimum_effect_size: float = 0.0,
) -> bool:
    """
    Decide whether the treatment should ship based on significance and effect size.

    This intentionally requires more than positive lift:
    - p-value must be below alpha
    - confidence interval must be entirely above zero
    - observed lift must meet the minimum practical effect size
    """
    if not math.isfinite(minimum_effect_size) or minimum_effect_size < 0:
        raise ValueError("minimum_effect_size must be finite and nonnegative.")
    return (
        result.p_value < result.alpha
        and result.ci_lower > 0
        and result.absolute_lift >= minimum_effect_size
    )


def interpret_ab_test_result(
    result: TwoProportionTestResult,
    *,
    minimum_effect_size: float = 0.0,
) -> str:
    """
    Produce a concise interpretation of an A/B test result.
    """
    if should_ship_treatment(
        result,
        minimum_effect_size=minimum_effect_size,
    ):
        return (
            "Ship treatment: the treatment shows statistically significant "
            "positive lift and meets the minimum practical effect size."
        )

    if result.p_value >= result.alpha:
        return (
            "Hold: the observed lift is not statistically significant, so the "
            "difference may be due to random variation."
        )

    if result.ci_lower <= 0 <= result.ci_upper:
        return (
            "Hold: the confidence interval crosses zero, so the true effect "
            "could be positive, neutral, or negative."
        )

    if result.absolute_lift < minimum_effect_size:
        return (
            "Hold: the result may be statistically significant, but the effect "
            "size is below the practical shipping threshold."
        )

    return "Hold: the treatment does not meet the shipping criteria."


def _validate_proportion_inputs(
    *,
    successes: int,
    total: int,
    label: str,
) -> None:
    if type(total) is not int or type(successes) is not int:
        raise ValueError(f"{label} counts must be integers, excluding booleans.")

    if total <= 0:
        raise ValueError(f"{label}_total must be positive.")

    if successes < 0:
        raise ValueError(f"{label}_successes cannot be negative.")

    if successes > total:
        raise ValueError(f"{label}_successes cannot exceed {label}_total.")


def _p_value_from_z(z_statistic: float, *, alternative: str) -> float:
    cdf = _standard_normal_cdf(z_statistic)

    if alternative == "two-sided":
        return 2 * min(cdf, 1 - cdf)

    if alternative == "greater":
        return 1 - cdf

    if alternative == "less":
        return cdf

    raise ValueError("alternative must be 'two-sided', 'greater', or 'less'.")


def _standard_normal_cdf(value: float) -> float:
    return 0.5 * (1 + math.erf(value / math.sqrt(2)))


def _z_critical_for_alpha(alpha: float) -> float:
    if isinstance(alpha, bool) or not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1.")
    return NormalDist().inv_cdf(1 - alpha / 2)