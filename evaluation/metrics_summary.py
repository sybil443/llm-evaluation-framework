import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MetricRecord:
    example_id: str
    metrics: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.example_id.strip():
            raise ValueError("example_id must be non-empty.")

        if not self.metrics:
            raise ValueError("metrics must be non-empty.")

        for metric_name, metric_value in self.metrics.items():
            if not metric_name.strip():
                raise ValueError("metric names must be non-empty.")

            if isinstance(metric_value, bool) or not isinstance(metric_value, int | float):
                raise TypeError("metric values must be numeric.")
            if not math.isfinite(metric_value):
                raise ValueError("metric values must be finite.")


@dataclass(frozen=True)
class MetricSummary:
    count: int
    metric_means: dict[str, float]
    slice_counts: dict[str, int]
    metric_names: list[str]


def summarize_metric_records(
    records: list[MetricRecord],
    *,
    slice_key: str | None = None,
) -> MetricSummary:
    if not records:
        raise ValueError("At least one metric record is required.")

    metric_totals: dict[str, float] = {}
    metric_counts: dict[str, int] = {}
    slice_counter: Counter[str] = Counter()

    for record in records:
        for metric_name, metric_value in record.metrics.items():
            metric_totals[metric_name] = (
                metric_totals.get(metric_name, 0.0) + float(metric_value)
            )
            metric_counts[metric_name] = metric_counts.get(metric_name, 0) + 1

        if slice_key is not None:
            slice_value = record.metadata.get(slice_key, "missing")
            slice_counter[str(slice_value)] += 1

    metric_means = {
        metric_name: metric_totals[metric_name] / metric_counts[metric_name]
        for metric_name in metric_totals
    }

    return MetricSummary(
        count=len(records),
        metric_means=metric_means,
        slice_counts=dict(slice_counter),
        metric_names=sorted(metric_means),
    )


def compare_metric_summaries(
    baseline: MetricSummary,
    challenger: MetricSummary,
) -> dict[str, float]:
    shared_metrics = set(baseline.metric_means) & set(challenger.metric_means)

    return {
        metric_name: challenger.metric_means[metric_name]
        - baseline.metric_means[metric_name]
        for metric_name in sorted(shared_metrics)
    }


def metric_summary_to_dict(summary: MetricSummary) -> dict[str, Any]:
    return {
        "count": summary.count,
        "metric_means": summary.metric_means,
        "slice_counts": summary.slice_counts,
        "metric_names": summary.metric_names,
    }