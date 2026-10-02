"""
Executable practical-vs-statistical-significance workflow.

Applies evaluation/significance.py's classification to two different
bootstrap comparisons already produced elsewhere in this repo:
  - The text-metric pipeline's overall and per-slice comparisons
    (evaluation/pipeline.py, via examples/demo_data.py's fixture).
  - The retrieval paired comparison (evaluation/retrieval_metrics.py, via
    examples/retrieval_eval_demo.py's fixture).

The point is reuse: the same classify_bootstrap_summary/classify_many
functions apply to both, even though the two comparisons come from
unrelated evaluation domains (text-metric lift vs. retrieval-ranking
lift) and were computed by different code paths that happen to share the
same mean/ci_lower/ci_upper bootstrap-summary shape.
"""
from evaluation.pipeline import evaluate
from evaluation.retrieval_metrics import compare_retrievers
from evaluation.significance import classify_bootstrap_summary, classify_many
from examples.demo_data import make_demo_request
from examples.retrieval_fixture import JUDGMENTS, bm25_rankings, build_index, term_overlap_rankings


def _verdict_row(name, result):
    return dict(
        name=name, verdict=result.verdict.value, point_estimate=result.point_estimate,
        ci_lower=result.ci_lower, ci_upper=result.ci_upper, minimum_effect=result.minimum_effect,
        is_statistically_significant=result.is_statistically_significant,
        is_practically_significant=result.is_practically_significant, direction=result.direction,
    )


def run_significance_demo():
    pipeline_result = evaluate(make_demo_request())
    pipeline_minimum_effect = pipeline_result["config"]["minimum_effect"]
    overall_verdict = classify_bootstrap_summary(
        pipeline_result["comparison"], minimum_effect=pipeline_minimum_effect)
    slice_verdicts = classify_many(
        {label: data for label, data in pipeline_result["slices"].items()},
        minimum_effect=pipeline_minimum_effect,
    )

    index = build_index()
    retrieval_comparison = compare_retrievers(
        term_overlap_rankings(index), bm25_rankings(index), JUDGMENTS)
    retrieval_minimum_effect = 0.05
    retrieval_verdicts = classify_many(
        retrieval_comparison.differences, minimum_effect=retrieval_minimum_effect)

    return dict(
        data_kind="synthetic",
        text_metric_significance=dict(
            source="evaluation/pipeline.py primary-metric comparison (examples/demo_data.py)",
            minimum_effect=pipeline_minimum_effect,
            overall=_verdict_row("overall", overall_verdict),
            slices=[_verdict_row(label, result) for label, result in slice_verdicts.items()],
        ),
        retrieval_significance=dict(
            source="evaluation/retrieval_metrics.py paired comparison (examples/retrieval_fixture.py)",
            minimum_effect=retrieval_minimum_effect,
            metrics=[_verdict_row(name, result) for name, result in retrieval_verdicts.items()],
        ),
        limitations=[
            "In this fixture, every individual slice classifies as "
            "significant_and_practical while the overall comparison "
            "classifies as practical_not_significant: the slices partly "
            "offset each other (technical regresses, support and transport "
            "improve), so the pooled interval is wider and crosses zero even "
            "though each subgroup's own interval does not. This is an "
            "expected property of subgroup bootstrapping, not a "
            "contradiction, and it is exactly why "
            "docs/practical_vs_statistical_significance_design.md calls "
            "slice intervals exploratory and unadjusted for multiple "
            "comparisons: five significance calls (one overall, three "
            "slices, and the retrieval side below) are read together here "
            "with no multiplicity correction across them.",
            "minimum_effect for the retrieval comparison (0.05) is chosen for "
            "this demo, not derived from any stated product requirement; a "
            "real minimum effect should come from what the retrieval result "
            "will be used for.",
            "Classification here reads confidence intervals and point "
            "estimates already computed elsewhere; it inherits every "
            "limitation of the bootstrap that produced them (independent "
            "sampling units, no multiplicity correction across slices or "
            "metrics), see docs/practical_vs_statistical_significance_design.md.",
            "With five retrieval queries and twenty-four pipeline examples, "
            "most intervals here are wide; 'statistically significant' at "
            "this sample size is a low bar, not a strong claim.",
        ],
    )


if __name__ == "__main__":
    import json

    print(json.dumps(run_significance_demo(), indent=2, sort_keys=True))
