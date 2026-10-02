import json

import pytest

from evaluation.judge_parser import JudgeParseError, parse_judge_output


def test_parse_judge_output_parses_valid_json() -> None:
    payload = {
        "example_id": "ex-1",
        "overall_score": 0.8,
        "criterion_scores": [
            {
                "criterion": "accuracy",
                "score": 0.9,
                "rationale": "Matches the reference.",
            }
        ],
    }

    result = parse_judge_output(json.dumps(payload))

    assert result == payload


def test_parse_judge_output_raises_for_malformed_json() -> None:
    with pytest.raises(JudgeParseError, match="not valid JSON"):
        parse_judge_output("{not json")


def test_parse_judge_output_raises_for_missing_required_field() -> None:
    payload = {
        "example_id": "ex-1",
        "overall_score": 0.8,
    }

    with pytest.raises(JudgeParseError, match="missing required fields"):
        parse_judge_output(json.dumps(payload))


def test_parse_judge_output_raises_when_criterion_scores_has_wrong_type() -> None:
    payload = {
        "example_id": "ex-1",
        "overall_score": 0.8,
        "criterion_scores": "not a list",
    }

    with pytest.raises(JudgeParseError, match="criterion_scores must be a list"):
        parse_judge_output(json.dumps(payload))

@pytest.mark.parametrize(
    "raw_output",
    [
        "[]",
        '"text"',
        "42",
        "null",
    ],
)
def test_parse_judge_output_rejects_non_object_json(
    raw_output: str,
) -> None:
    with pytest.raises(
        JudgeParseError,
        match="must be a JSON object",
    ):
        parse_judge_output(raw_output)