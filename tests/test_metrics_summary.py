import pytest

from evaluation.metrics_summary import (
    MetricRecord,
    MetricSummary,
    compare_metric_summaries,
    metric_summary_to_dict,
    summarize_metric_records,
)


def test_metric_record_rejects_blank_example_id() -> None:
    with pytest.raises(ValueError, match="example_id"):
        MetricRecord(example_id="   ", metrics={"rouge_l": 0.8})


def test_metric_record_rejects_empty_metrics() -> None:
    with pytest.raises(ValueError, match="metrics"):
        MetricRecord(example_id="ex-001", metrics={})


def test_metric_record_rejects_blank_metric_name() -> None:
    with pytest.raises(ValueError, match="metric names"):
        MetricRecord(example_id="ex-001", metrics={"   ": 0.8})


def test_metric_record_rejects_non_numeric_metric_value() -> None:
    with pytest.raises(TypeError, match="metric values"):
        MetricRecord(example_id="ex-001", metrics={"rouge_l": "high"})


def test_summarize_metric_records_calculates_metric_means() -> None:
    records = [
        MetricRecord(example_id="ex-001", metrics={"rouge_l": 0.8, "cosine": 0.9}),
        MetricRecord(example_id="ex-002", metrics={"rouge_l": 0.6, "cosine": 0.7}),
    ]

    summary = summarize_metric_records(records)

    assert isinstance(summary, MetricSummary)
    assert summary.count == 2
    assert summary.metric_means == {
        "rouge_l": 0.7,
        "cosine": 0.8,
    }
    assert summary.metric_names == ["cosine", "rouge_l"]


def test_summarize_metric_records_counts_slices() -> None:
    records = [
        MetricRecord(
            example_id="ex-001",
            metrics={"rouge_l": 0.8},
            metadata={"slice": "claims"},
        ),
        MetricRecord(
            example_id="ex-002",
            metrics={"rouge_l": 0.6},
            metadata={"slice": "claims"},
        ),
        MetricRecord(
            example_id="ex-003",
            metrics={"rouge_l": 0.9},
            metadata={"slice": "billing"},
        ),
    ]

    summary = summarize_metric_records(records, slice_key="slice")

    assert summary.slice_counts == {
        "claims": 2,
        "billing": 1,
    }


def test_summarize_metric_records_counts_missing_slice() -> None:
    records = [
        MetricRecord(example_id="ex-001", metrics={"rouge_l": 0.8}),
    ]

    summary = summarize_metric_records(records, slice_key="slice")

    assert summary.slice_counts == {"missing": 1}


def test_summarize_metric_records_rejects_empty_records() -> None:
    with pytest.raises(ValueError, match="At least one metric record"):
        summarize_metric_records([])


def test_compare_metric_summaries_returns_challenger_minus_baseline() -> None:
    baseline = MetricSummary(
        count=2,
        metric_means={"rouge_l": 0.6, "cosine": 0.7},
        slice_counts={},
        metric_names=["cosine", "rouge_l"],
    )
    challenger = MetricSummary(
        count=2,
        metric_means={"rouge_l": 0.75, "cosine": 0.8},
        slice_counts={},
        metric_names=["cosine", "rouge_l"],
    )

    comparison = compare_metric_summaries(baseline, challenger)

    assert comparison == {
        "cosine": pytest.approx(0.1),
        "rouge_l": pytest.approx(0.15),
    }


def test_compare_metric_summaries_uses_only_shared_metrics() -> None:
    baseline = MetricSummary(
        count=2,
        metric_means={"rouge_l": 0.6},
        slice_counts={},
        metric_names=["rouge_l"],
    )
    challenger = MetricSummary(
        count=2,
        metric_means={"rouge_l": 0.75, "cosine": 0.8},
        slice_counts={},
        metric_names=["cosine", "rouge_l"],
    )

    comparison = compare_metric_summaries(baseline, challenger)

    assert comparison == {"rouge_l": pytest.approx(0.15)}


def test_metric_summary_to_dict() -> None:
    summary = MetricSummary(
        count=2,
        metric_means={"rouge_l": 0.7},
        slice_counts={"claims": 2},
        metric_names=["rouge_l"],
    )

    assert metric_summary_to_dict(summary) == {
        "count": 2,
        "metric_means": {"rouge_l": 0.7},
        "slice_counts": {"claims": 2},
        "metric_names": ["rouge_l"],
    }