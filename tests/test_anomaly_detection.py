import pytest

from evaluation.anomaly_detection import (
    AnomalyRecord,
    detect_anomalies,
    detect_outliers,
    metric_delta_records,
    metric_records,
    modified_z_scores,
    response_length_records,
)


def test_modified_z_scores_flags_single_outlier() -> None:
    values = [1.0, 1.1, 0.9, 1.05, 0.95, 10.0]

    scores = modified_z_scores(values)

    assert len(scores) == len(values)
    assert abs(scores[-1]) > abs(scores[0])
    assert abs(scores[-1]) >= 3.5


def test_modified_z_scores_all_zero_for_constant_values() -> None:
    assert modified_z_scores([2.0, 2.0, 2.0, 2.0]) == [0.0, 0.0, 0.0, 0.0]


def test_modified_z_scores_rejects_fewer_than_two_values() -> None:
    with pytest.raises(ValueError, match="two values"):
        modified_z_scores([1.0])


def test_detect_outliers_flags_the_extreme_value() -> None:
    records = [("a", 1.0, "s"), ("b", 1.1, "s"), ("c", 0.9, "s"),
               ("d", 1.05, "s"), ("e", 0.95, "s"), ("f", 10.0, "s")]

    anomalies = detect_outliers(records, signal="test_signal", group_by_slice=False)

    assert len(anomalies) == 1
    assert anomalies[0].example_id == "f"
    assert anomalies[0].signal == "test_signal"
    assert isinstance(anomalies[0], AnomalyRecord)


def test_detect_outliers_rejects_non_positive_threshold() -> None:
    records = [("a", 1.0, "s"), ("b", 2.0, "s")]

    with pytest.raises(ValueError, match="threshold"):
        detect_outliers(records, signal="x", threshold=0)


def test_detect_outliers_rejects_empty_records() -> None:
    with pytest.raises(ValueError, match="not be empty"):
        detect_outliers([], signal="x")


def test_detect_outliers_rejects_duplicate_example_ids() -> None:
    records = [("a", 1.0, "s"), ("a", 2.0, "s")]

    with pytest.raises(ValueError, match="duplicate"):
        detect_outliers(records, signal="x")


def test_detect_outliers_without_grouping_requires_two_records() -> None:
    with pytest.raises(ValueError, match="two records"):
        detect_outliers([("a", 1.0, "s")], signal="x", group_by_slice=False)


def test_detect_outliers_groups_by_slice_by_default() -> None:
    # Slice "s1" has a real outlier; slice "s2" is uniform and small.
    records = [
        ("a", 1.0, "s1"), ("b", 1.1, "s1"), ("c", 0.9, "s1"),
        ("d", 1.0, "s1"), ("e", 0.95, "s1"), ("f", 10.0, "s1"),
        ("g", 5.0, "s2"), ("h", 5.0, "s2"),
    ]

    anomalies = detect_outliers(records, signal="x")

    assert [a.example_id for a in anomalies] == ["f"]


def test_detect_outliers_skips_slice_groups_smaller_than_two() -> None:
    records = [("a", 1.0, "solo"), ("b", 1.0, "pair"), ("c", 1.0, "pair")]

    # No error even though the "solo" group has only one member.
    assert detect_outliers(records, signal="x") == []


def make_rows() -> list[dict]:
    base = dict(baseline_metrics={"rouge_l_f1": 0.8}, challenger_metrics={"rouge_l_f1": 0.82},
               baseline_response="a reasonably normal response here", challenger_response="a reasonably normal response too")
    rows = []
    for i in range(6):
        row = dict(base)
        row["example_id"] = f"ex-{i}"
        row["slice"] = "only"
        row["baseline_metrics"] = {"rouge_l_f1": 0.8 + i * 0.01}
        row["challenger_metrics"] = {"rouge_l_f1": 0.82 + i * 0.01}
        rows.append(row)
    # One genuine outlier: very low challenger score and a very short response.
    outlier = dict(base)
    outlier["example_id"] = "ex-outlier"
    outlier["slice"] = "only"
    outlier["baseline_metrics"] = {"rouge_l_f1": 0.8}
    outlier["challenger_metrics"] = {"rouge_l_f1": 0.01}
    outlier["challenger_response"] = "no"
    rows.append(outlier)
    return rows


def test_metric_records_extracts_example_id_value_and_slice() -> None:
    rows = make_rows()

    records = metric_records(rows, "challenger", "rouge_l_f1")

    assert records[0] == ("ex-0", 0.82, "only")


def test_metric_delta_records_computes_challenger_minus_baseline() -> None:
    rows = [dict(example_id="ex-1", slice="s",
                baseline_metrics={"m": 0.5}, challenger_metrics={"m": 0.7})]

    records = metric_delta_records(rows, "m")

    assert records == [("ex-1", pytest.approx(0.2), "s")]


def test_response_length_records_counts_tokens() -> None:
    rows = [dict(example_id="ex-1", slice="s", challenger_response="one two three")]

    records = response_length_records(rows, "challenger")

    assert records == [("ex-1", 3.0, "s")]


def test_detect_anomalies_flags_the_planted_outlier() -> None:
    rows = make_rows()

    report = detect_anomalies(rows)

    flagged_ids = {a.example_id for a in report.anomalies}
    assert "ex-outlier" in flagged_ids
    assert report.n_examples == len(rows)
    assert set(report.signals) == {
        "challenger_rouge_l_f1_outlier", "baseline_rouge_l_f1_outlier",
        "rouge_l_f1_delta_outlier", "challenger_response_length_outlier",
    }


def test_detect_anomalies_rejects_empty_rows() -> None:
    with pytest.raises(ValueError, match="not be empty"):
        detect_anomalies([])


def test_detect_anomalies_counts_by_signal_and_slice_are_consistent() -> None:
    rows = make_rows()

    report = detect_anomalies(rows)

    assert sum(report.counts_by_signal.values()) == len(report.anomalies)
    assert sum(report.counts_by_slice.values()) == len(report.anomalies)
