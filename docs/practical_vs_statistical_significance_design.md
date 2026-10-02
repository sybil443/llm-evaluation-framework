# Statistical comparison and decision policy

Status: paired bootstrap and independent-group z-test utilities are implemented.
The sample datasets/counts are synthetic demonstrations, not measured model lift.

## Reusable significance classification

`evaluation/significance.py` pulls the practical-vs-statistical check
described in this document out of `evaluation/pipeline.py`'s inline
control flow into a single, independently testable function
(`classify_significance`, plus `classify_bootstrap_summary`/
`classify_many` adapters for this repo's bootstrap-summary dict shape).
It classifies any point estimate with a confidence interval into one of
four verdicts:

| Verdict | CI excludes zero? | \|point estimate\| ≥ minimum_effect? |
|---|---|---|
| `significant_and_practical` | yes | yes |
| `significant_not_practical` | yes | no |
| `practical_not_significant` | no | yes |
| `inconclusive` | no | no |

This is applied in `examples/significance_demo.py` to two independent
bootstrap comparisons: the text-metric pipeline's overall and per-slice
comparison (`evaluation/pipeline.py`, via `examples/demo_data.py`), and
the retrieval paired comparison (`evaluation/retrieval_metrics.py`, via
`examples/retrieval_fixture.py`) — the same classification function
applied to two unrelated evaluation domains that happen to produce the
same mean/ci_lower/ci_upper bootstrap shape.

On the demo fixture, every individual slice classifies as
`significant_and_practical` while the pooled overall comparison
classifies as `practical_not_significant` (the technical slice regresses
while support and transport improve, so the pooled interval is wider and
crosses zero even though each subgroup's own interval does not). This is
an expected property of subgroup bootstrapping, not a contradiction, and
it is exactly the reason slice intervals are called exploratory and
unadjusted for multiple comparisons below: reading five significance
calls (one overall, three slices, several retrieval metrics) together
with no multiplicity correction across them is itself a limitation the
demo's output states explicitly.

`evaluation/significance.py` does not compute confidence intervals; it
only classifies ones already computed elsewhere, so it inherits whatever
caveats apply to the code that produced them (see below, and
`evaluation/retrieval_metrics.py`'s own module docstring for the
retrieval side).

## Paired evaluation

The pipeline validates exact ID-set equality and orders IDs before comparison.
For each example, difference = challenger ROUGE-L minus baseline ROUGE-L.
The bootstrap samples those paired differences with replacement using NumPy's
seeded generator. Linear empirical quantiles form a two-sided percentile interval.
One canonical implementation backs the reusable bootstrap entry points.

`positive_resample_fraction` is the empirical fraction of bootstrap mean
differences above zero. It is not a posterior probability, a p-value, or the
probability that the true challenger model is superior.

Pairs must be independent sampling units. Multiple outputs for a user/document
require grouped or cluster-aware sampling, which is not implemented. Small or
constant samples can yield misleadingly narrow intervals. Minimum counts are
review guardrails, not proof of sufficient statistical power.

## Decision policy

- INSUFFICIENT_EVIDENCE: total or a slice is below the configured minimum.
- HOLD: the primary interval includes zero or is negative, the point estimate is
  below the practical threshold, a slice point estimate regresses beyond its
  guardrail, or data are marked synthetic.
- REVIEW_CANDIDATE: all those offline gates pass; human and operational review
  still required. This is not automatic authorization to deploy.

The practical threshold applies to the observed effect, not its lower confidence
bound. Slice intervals are exploratory and unadjusted for multiple comparisons.
All thresholds should be specified before looking at actual benchmark results.
No equivalence, non-inferiority, sequential testing, or multiplicity correction
is claimed by this implementation.

## Independent-group A/B testing

`examples/ab_demo.py` uses separate illustrative Bernoulli groups. The utility
uses a pooled z-test and an unpooled normal-approximation interval. Counts must
be integers, and inadequate expected/observed success-failure cells are rejected.
Critical values use the requested alpha directly, without rounding to a lookup key.
One-sided p-values, if requested, still accompany a two-sided interval. Because
the test and interval use different variance estimates, they are not exact duals.
For sparse/extreme proportions, use a suitable exact or score-based method instead.
Do not use this independent-group utility on paired responses to identical prompts.