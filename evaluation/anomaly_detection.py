"""
Anomalous-output detection: robust statistical outlier flags over
evaluation rows (as produced by evaluation.pipeline.evaluate).

Uses the modified z-score (Iglewicz & Hoaglin): a robust score based on
the median and median absolute deviation (MAD) rather than the mean and
standard deviation, so a few extreme examples don't hide each other or
skew the threshold that would flag them. Threshold 3.5 is the commonly
cited default for this method, not a value tuned on this repo's data.

Limitations, stated up front:
  - This flags statistical outliers in metric scores, response length, or
    baseline-to-challenger deltas. An outlier is not necessarily a model
    failure (a genuinely excellent or unusually long response is also an
    outlier), and a real failure is not necessarily an outlier (a
    consistently mediocre model produces no outliers at all).
  - The modified z-score needs enough spread to be meaningful; with very
    few examples, or examples that are nearly identical, few or no points
    can be flagged regardless of `threshold`. This module does not lower
    the bar to force a result.
  - Signals are computed independently per metric/side; nothing here
    models multivariate anomalies (e.g., a jointly unusual combination of
    two metrics that is not extreme on either one alone).
  - This complements, but does not replace, evaluation/pipeline.py's
    fixed-threshold heuristic tags (`lexical/low_reference_overlap`,
    `comparison/example_regression`): those use configured cutoffs;
    this uses the row set's own distribution, so what counts as unusual
    depends on the batch being evaluated.
"""
from collections import Counter
from dataclasses import dataclass
from typing import Any

from evaluation.search_index import search_tokens

DEFAULT_THRESHOLD = 3.5
_MODIFIED_Z_CONSTANT = 0.6745


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def modified_z_scores(values: list[float]) -> list[float]:
    """
    Robust z-scores using the median and median absolute deviation (MAD).

    Falls back to the mean absolute deviation around the median when MAD
    is zero (more than half the values are identical), to avoid dividing
    by zero on a majority-tied sample. If that is also zero (every value
    is identical), every score is 0.0: with no spread at all, nothing can
    be an outlier.
    """
    if len(values) < 2:
        raise ValueError("At least two values are required to compute z-scores.")
    center = _median(values)
    deviations = [abs(x - center) for x in values]
    spread = _median(deviations)
    if spread == 0:
        spread = sum(deviations) / len(deviations)
    if spread == 0:
        return [0.0] * len(values)
    return [_MODIFIED_Z_CONSTANT * (x - center) / spread for x in values]


@dataclass(frozen=True)
class AnomalyRecord:
    example_id: str
    signal: str
    value: float
    modified_z_score: float
    slice: str | None = None


def _validate_records(records: list[tuple[str, float, Any]]) -> None:
    if not records:
        raise ValueError("records must not be empty.")
    ids = [example_id for example_id, _, _ in records]
    if len(set(ids)) != len(ids):
        raise ValueError("Records must not contain duplicate example ids.")


def _flat_outliers(
    records: list[tuple[str, float, Any]], *, signal: str, threshold: float,
) -> list[AnomalyRecord]:
    if len(records) < 2:
        return []
    values = [value for _, value, _ in records]
    z_scores = modified_z_scores(values)
    return [
        AnomalyRecord(example_id=example_id, signal=signal, value=value,
                     modified_z_score=z, slice=slice_label)
        for (example_id, value, slice_label), z in zip(records, z_scores)
        if abs(z) >= threshold
    ]


def detect_outliers(
    records: list[tuple[str, float, Any]], *, signal: str, threshold: float = DEFAULT_THRESHOLD,
    group_by_slice: bool = True,
) -> list[AnomalyRecord]:
    """
    Flag records whose modified z-score magnitude is at or above `threshold`.

    `records` is a list of (example_id, value, slice_label) tuples.

    When `group_by_slice` is True (the default), the z-score is computed
    separately within each slice group (records sharing the same
    slice_label), so an example is flagged only when it is unusual
    relative to its own slice peers. Without this, one slice that is
    deliberately or genuinely different as a whole (which
    evaluation/pipeline.py's per-slice bootstrap comparison already
    detects on its own terms) can dominate a global distribution and get
    almost entirely flagged as "outliers," which mostly just re-states
    that the slices differ rather than finding unusual examples within
    one. A slice group with fewer than two records contributes no
    z-score (nothing is computable) and is silently skipped rather than
    treated as an error, since too little data in one slice is expected,
    not a caller mistake. Pass `group_by_slice=False` to score every
    record against one global distribution instead.
    """
    if threshold <= 0:
        raise ValueError("threshold must be positive.")
    _validate_records(records)
    if not group_by_slice:
        if len(records) < 2:
            raise ValueError("At least two records are required to detect outliers.")
        return _flat_outliers(records, signal=signal, threshold=threshold)
    groups: dict[Any, list[tuple[str, float, Any]]] = {}
    for record in records:
        groups.setdefault(record[2], []).append(record)
    anomalies = []
    for group_records in groups.values():
        anomalies.extend(_flat_outliers(group_records, signal=signal, threshold=threshold))
    anomalies.sort(key=lambda anomaly: anomaly.example_id)
    return anomalies


def metric_records(rows: list[dict], side: str, metric: str) -> list[tuple[str, float, Any]]:
    """Extract (example_id, metric value, slice) from pipeline rows for one side."""
    return [(row["example_id"], row[f"{side}_metrics"][metric], row.get("slice")) for row in rows]


def metric_delta_records(rows: list[dict], metric: str) -> list[tuple[str, float, Any]]:
    """Extract (example_id, challenger - baseline metric delta, slice) from pipeline rows."""
    return [
        (row["example_id"], row["challenger_metrics"][metric] - row["baseline_metrics"][metric],
         row.get("slice"))
        for row in rows
    ]


def response_length_records(rows: list[dict], side: str) -> list[tuple[str, float, Any]]:
    """Extract (example_id, token count, slice) for one side's response text."""
    return [
        (row["example_id"], float(len(search_tokens(row[f"{side}_response"]))), row.get("slice"))
        for row in rows
    ]


@dataclass(frozen=True)
class AnomalyReport:
    n_examples: int
    signals: tuple[str, ...]
    anomalies: list[AnomalyRecord]
    counts_by_signal: dict[str, int]
    counts_by_slice: dict[str, int]


def detect_anomalies(
    rows: list[dict], *, metric: str = "rouge_l_f1", threshold: float = DEFAULT_THRESHOLD,
    group_by_slice: bool = True,
) -> AnomalyReport:
    """
    Run every built-in anomaly signal over `rows` and combine the results.

    Signals: challenger metric outliers, baseline metric outliers,
    challenger-minus-baseline metric-delta outliers, and challenger
    response-length outliers. `rows` must have at least one entry;
    `group_by_slice` is passed through to `detect_outliers` (see its
    docstring for why grouping by slice is the default).
    """
    if not rows:
        raise ValueError("rows must not be empty.")
    signal_records = {
        f"challenger_{metric}_outlier": metric_records(rows, "challenger", metric),
        f"baseline_{metric}_outlier": metric_records(rows, "baseline", metric),
        f"{metric}_delta_outlier": metric_delta_records(rows, metric),
        "challenger_response_length_outlier": response_length_records(rows, "challenger"),
    }
    anomalies: list[AnomalyRecord] = []
    for signal, records in signal_records.items():
        anomalies.extend(detect_outliers(records, signal=signal, threshold=threshold,
                                         group_by_slice=group_by_slice))
    counts_by_signal = dict(Counter(a.signal for a in anomalies))
    counts_by_slice = dict(Counter(a.slice for a in anomalies if a.slice is not None))
    return AnomalyReport(
        n_examples=len(rows), signals=tuple(signal_records), anomalies=anomalies,
        counts_by_signal=counts_by_signal, counts_by_slice=counts_by_slice,
    )
