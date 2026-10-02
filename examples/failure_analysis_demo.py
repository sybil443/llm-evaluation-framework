"""
Executable failure-analysis workflow: structured failure taxonomy plus
anomalous-output detection, run over the rows the pipeline already
produces for the authored demo evaluation (examples/demo_data.py).

This is a post-hoc analysis layer over evaluation.pipeline.evaluate()'s
output rows, kept separate from the pipeline's own returned dict (which
is committed and diffed in CI as examples/example_report.md) rather than
folded into it, matching how examples/retrieval_eval_demo.py is kept
separate from the pipeline.
"""
from evaluation.anomaly_detection import DEFAULT_THRESHOLD, detect_anomalies
from evaluation.failure_taxonomy import analyze_failure_tags, load_taxonomy
from evaluation.pipeline import evaluate
from examples.demo_data import make_demo_request


def run_failure_analysis_demo():
    result = evaluate(make_demo_request())
    rows = result["rows"]
    taxonomy = load_taxonomy()
    taxonomy_report = analyze_failure_tags(rows, taxonomy)
    anomaly_report = detect_anomalies(rows, metric="rouge_l_f1")
    return dict(
        data_kind="synthetic",
        source_run_id=result["run_id"],
        n_rows=len(rows),
        failure_taxonomy=dict(
            taxonomy_source="examples/failure_taxonomy_example.json",
            total_rows=taxonomy_report.total_rows,
            flagged_rows=taxonomy_report.flagged_rows,
            tag_counts=taxonomy_report.tag_counts,
            category_counts=taxonomy_report.category_counts,
            counts_by_slice=taxonomy_report.counts_by_slice,
            unknown_tags=list(taxonomy_report.unknown_tags),
        ),
        anomalous_outputs=dict(
            metric="rouge_l_f1", threshold=DEFAULT_THRESHOLD,
            signals=list(anomaly_report.signals),
            counts_by_signal=anomaly_report.counts_by_signal,
            counts_by_slice=anomaly_report.counts_by_slice,
            anomalies=[
                dict(example_id=a.example_id, signal=a.signal, value=a.value,
                     modified_z_score=a.modified_z_score, slice=a.slice)
                for a in anomaly_report.anomalies
            ],
        ),
        limitations=[
            "Taxonomy and anomaly detection run over the 24-example authored "
            "fixture from examples/demo_data.py; too small to characterize a "
            "real model's failure modes or to tune an outlier threshold.",
            "Anomaly signals are per-metric, per-side statistical outlier "
            "flags (see evaluation/anomaly_detection.py's module docstring "
            "for what modified z-scores do and do not mean); they are "
            "candidates for human review, not verified failures.",
            "The taxonomy validates and categorizes tags the pipeline "
            "already assigned; it does not independently judge whether a "
            "response actually failed.",
        ],
    )


if __name__ == "__main__":
    import json

    print(json.dumps(run_failure_analysis_demo(), indent=2, sort_keys=True))
