import json
import math

import pytest
from pydantic import ValidationError

from evaluation.judge_calibration import CalibrationExample
from evaluation.judge_parser import JudgeParseError, parse_judge_output
from evaluation.ab_testing import confidence_interval_for_rate_difference, two_proportion_z_test
from evaluation.rubric_schema import parse_rubric_schema
from evaluation.statistics import bootstrap_summary, paired_summary
from examples.judge_workflow import RUBRIC


@pytest.mark.parametrize("values", [[float("nan")], [float("inf")], [True], ["0.5"]])
def test_non_numeric_or_nonfinite_bootstrap_inputs_rejected(values):
    with pytest.raises(ValueError):
        bootstrap_summary(values)


@pytest.mark.parametrize("n", [0, -1, True, 1.5])
def test_invalid_resample_counts_rejected(n):
    with pytest.raises(ValueError):
        paired_summary([0.1], [0.2], n_resamples=n)


def test_constant_difference_has_exact_interval():
    result = paired_summary([1, 2, 3], [3, 4, 5], n_resamples=100)
    assert result["mean_difference"] == 2
    assert result["ci_lower"] == result["ci_upper"] == 2
    assert result["positive_resample_fraction"] == 1
    # positive_resample_fraction is descriptive, not a posterior probability
    # (see evaluation/statistics.py); it must never be reported under that name.
    assert "probability_b_better" not in result


def test_confidence_changes_interval_and_is_recorded():
    low = bootstrap_summary([0, 0.1, 0.3, 1, 2], 1000, 0.8)
    high = bootstrap_summary([0, 0.1, 0.3, 1, 2], 1000, 0.99)
    assert high["ci_lower"] <= low["ci_lower"]
    assert high["ci_upper"] >= low["ci_upper"]
    assert high["confidence_level"] == 0.99


@pytest.mark.parametrize("counts", [
    dict(control_successes=True, control_total=20, treatment_successes=5, treatment_total=20),
    dict(control_successes=1, control_total=5, treatment_successes=2, treatment_total=5),
])
def test_ab_test_rejects_invalid_counts_or_poor_normal_approximation(counts):
    with pytest.raises(ValueError):
        two_proportion_z_test(**counts)


def valid_payload():
    return dict(example_id="x", overall_score=1.0, criterion_scores=[
        dict(criterion="correctness", score=1, rationale="Fixture"),
        dict(criterion="clarity", score=5, rationale="Fixture"),
    ])


def test_parser_recomputes_score_from_validated_rubric():
    result = parse_judge_output(json.dumps(valid_payload()), expected_example_id="x",
                                rubric=parse_rubric_schema(RUBRIC))
    assert result["overall_score"] == 0.25


@pytest.mark.parametrize("mutation", ["wrong_id", "duplicate", "missing", "unknown", "range", "nan", "rationale", "bool"])
def test_invalid_judge_payloads_rejected(mutation):
    value = valid_payload()
    if mutation == "wrong_id": value["example_id"] = "other"
    elif mutation == "duplicate": value["criterion_scores"].append(value["criterion_scores"][0])
    elif mutation == "missing": value["criterion_scores"].pop()
    elif mutation == "unknown": value["criterion_scores"][0]["criterion"] = "invented"
    elif mutation == "range": value["criterion_scores"][0]["score"] = 6
    elif mutation == "nan": value["criterion_scores"][0]["score"] = float("nan")
    elif mutation == "rationale": value["criterion_scores"][0]["rationale"] = " "
    elif mutation == "bool": value["criterion_scores"][0]["score"] = True
    with pytest.raises(JudgeParseError):
        parse_judge_output(json.dumps(value), expected_example_id="x", rubric=parse_rubric_schema(RUBRIC))


def test_duplicate_json_keys_rejected():
    with pytest.raises(JudgeParseError, match="Duplicate JSON key"):
        parse_judge_output('{"example_id":"a","example_id":"b"}')


def test_nan_calibration_and_duplicate_rubric_rejected():
    with pytest.raises(ValueError):
        CalibrationExample("x", "yes", "yes", float("nan"), 1)
    data = json.loads(json.dumps(RUBRIC))
    data["criteria"][1]["name"] = "correctness"
    with pytest.raises(ValidationError):
        parse_rubric_schema(data)