"""
Practical vs. statistical significance: one reusable classification.

`evaluation/pipeline.py`'s decision policy already combines a
statistical check (does the bootstrap CI exclude zero?) with a practical
check (is the point estimate at least `config.minimum_effect`?) inline in
its own control flow. This module pulls that combination out into a
single, independently testable classification usable by any bootstrap
result in this repo, not only the text-metric pipeline: it is applied
here to both the pipeline's overall/slice comparisons and
`evaluation/retrieval_metrics.py`'s paired retriever comparison.

Definitions:
  - Statistically significant: the confidence interval excludes zero
    (entirely positive or entirely negative). This says the direction of
    the observed effect is unlikely to be a sampling artifact at the
    interval's confidence level; it says nothing about the effect's size.
  - Practically significant: the point estimate's magnitude is at least
    `minimum_effect`. This says the effect is big enough to matter for
    some stated purpose; it says nothing about measurement uncertainty.

The two are independent by design, matching
docs/practical_vs_statistical_significance_design.md: a large observed
difference in a small sample can be practically significant but not
statistically significant (the CI still includes zero), and a tiny but
very precisely measured difference can be statistically significant
without being practically significant.

Limitations, stated up front:
  - This module does not compute confidence intervals; it only
    classifies ones already computed (by
    evaluation.statistics.bootstrap_summary/paired_summary or anything
    else with the same mean/ci_lower/ci_upper shape). Interval-computation
    caveats (independence assumptions, no multiplicity correction) belong
    to that code, not this one.
  - `minimum_effect` is a threshold the caller must choose and justify for
    the metric and decision at hand; this module has no default that
    means anything universally, so it defaults to 0.0 (statistical
    significance alone), which callers should override.
  - "Statistically significant" here is a bootstrap-CI-excludes-zero
    check, not a p-value from a specific hypothesis test; the same
    caveats documented for the bootstrap in evaluation/statistics.py
    apply (no posterior probability claim, independent-sampling-unit
    assumption).
"""
import math
from dataclasses import dataclass
from enum import Enum
from typing import Any


class SignificanceVerdict(str, Enum):
    SIGNIFICANT_AND_PRACTICAL = "significant_and_practical"
    SIGNIFICANT_NOT_PRACTICAL = "significant_not_practical"
    PRACTICAL_NOT_SIGNIFICANT = "practical_not_significant"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class SignificanceResult:
    verdict: SignificanceVerdict
    point_estimate: float
    ci_lower: float
    ci_upper: float
    minimum_effect: float
    is_statistically_significant: bool
    is_practically_significant: bool
    direction: str


def _check_finite(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number.")


def classify_significance(
    point_estimate: float, ci_lower: float, ci_upper: float, *, minimum_effect: float = 0.0,
) -> SignificanceResult:
    """
    Classify one effect estimate as practically/statistically significant.

    `point_estimate` is typically a bootstrap mean or mean difference;
    `ci_lower`/`ci_upper` bound its confidence interval at whatever
    confidence level that interval was built with. `minimum_effect` is
    the smallest |point_estimate| the caller considers to matter in
    practice; it must be non-negative.
    """
    for name, value in (("point_estimate", point_estimate), ("ci_lower", ci_lower), ("ci_upper", ci_upper)):
        _check_finite(name, value)
    if ci_lower > ci_upper:
        raise ValueError("ci_lower must not exceed ci_upper.")
    if isinstance(minimum_effect, bool) or not isinstance(minimum_effect, (int, float)) or minimum_effect < 0:
        raise ValueError("minimum_effect must be a non-negative number.")

    is_significant = ci_lower > 0 or ci_upper < 0
    is_practical = abs(point_estimate) >= minimum_effect
    if is_significant and is_practical:
        verdict = SignificanceVerdict.SIGNIFICANT_AND_PRACTICAL
    elif is_significant:
        verdict = SignificanceVerdict.SIGNIFICANT_NOT_PRACTICAL
    elif is_practical:
        verdict = SignificanceVerdict.PRACTICAL_NOT_SIGNIFICANT
    else:
        verdict = SignificanceVerdict.INCONCLUSIVE
    direction = "positive" if point_estimate > 0 else "negative" if point_estimate < 0 else "zero"
    return SignificanceResult(
        verdict=verdict, point_estimate=point_estimate, ci_lower=ci_lower, ci_upper=ci_upper,
        minimum_effect=minimum_effect, is_statistically_significant=is_significant,
        is_practically_significant=is_practical, direction=direction,
    )


def classify_bootstrap_summary(summary: dict[str, Any], *, minimum_effect: float = 0.0) -> SignificanceResult:
    """
    Classify the output of evaluation.statistics.bootstrap_summary or
    paired_summary directly, reading `mean`/`mean_difference` and
    `ci_lower`/`ci_upper` from it.
    """
    if "mean_difference" in summary:
        point = summary["mean_difference"]
    elif "mean" in summary:
        point = summary["mean"]
    else:
        raise ValueError("summary must contain 'mean' or 'mean_difference'.")
    if "ci_lower" not in summary or "ci_upper" not in summary:
        raise ValueError("summary must contain 'ci_lower' and 'ci_upper'.")
    return classify_significance(point, summary["ci_lower"], summary["ci_upper"], minimum_effect=minimum_effect)


def classify_many(
    summaries: dict[str, dict[str, Any]], *, minimum_effect: float = 0.0,
) -> dict[str, SignificanceResult]:
    """Classify a dict of bootstrap summaries (e.g. per-metric or per-slice) at once."""
    if not summaries:
        raise ValueError("summaries must not be empty.")
    return {name: classify_bootstrap_summary(summary, minimum_effect=minimum_effect)
            for name, summary in summaries.items()}
