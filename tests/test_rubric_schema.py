from pathlib import Path

import pytest
from pydantic import ValidationError

from evaluation.rubric_schema import (
    load_rubric_schema_yaml,
    parse_rubric_schema,
    rubric_schema_json_schema,
    rubric_schema_to_judge_criteria,
)


def make_valid_rubric_payload() -> dict:
    return {
        "rubric_id": "llm-judge-rubric",
        "version": "0.1",
        "description": "Rubric for evaluating LLM responses.",
        "criteria": [
            {
                "name": "correctness",
                "description": "The response should be factually correct.",
                "weight": 0.4,
                "min_score": 1.0,
                "max_score": 5.0,
            },
            {
                "name": "relevance",
                "description": "The response should directly answer the prompt.",
                "weight": 0.3,
                "min_score": 1.0,
                "max_score": 5.0,
            },
            {
                "name": "clarity",
                "description": "The response should be easy to understand.",
                "weight": 0.3,
                "min_score": 1.0,
                "max_score": 5.0,
            },
        ],
    }


def test_parse_rubric_schema_accepts_valid_payload() -> None:
    rubric = parse_rubric_schema(make_valid_rubric_payload())

    assert rubric.rubric_id == "llm-judge-rubric"
    assert rubric.version == "0.1"
    assert len(rubric.criteria) == 3
    assert rubric.criteria[0].name == "correctness"


def test_parse_rubric_schema_rejects_blank_rubric_id() -> None:
    payload = make_valid_rubric_payload()
    payload["rubric_id"] = "   "

    with pytest.raises(ValidationError, match="Field must not be blank"):
        parse_rubric_schema(payload)


def test_parse_rubric_schema_rejects_empty_criteria() -> None:
    payload = make_valid_rubric_payload()
    payload["criteria"] = []

    with pytest.raises(ValidationError):
        parse_rubric_schema(payload)


def test_parse_rubric_schema_rejects_weights_that_do_not_sum_to_one() -> None:
    payload = make_valid_rubric_payload()
    payload["criteria"][0]["weight"] = 0.8

    with pytest.raises(ValidationError, match="weights must sum to 1.0"):
        parse_rubric_schema(payload)


def test_parse_rubric_schema_rejects_negative_weight() -> None:
    payload = make_valid_rubric_payload()
    payload["criteria"][0]["weight"] = -0.1

    with pytest.raises(ValidationError, match="weight must be positive"):
        parse_rubric_schema(payload)


def test_parse_rubric_schema_rejects_invalid_score_range() -> None:
    payload = make_valid_rubric_payload()
    payload["criteria"][0]["min_score"] = 5.0
    payload["criteria"][0]["max_score"] = 1.0

    with pytest.raises(ValidationError, match="min_score must be less"):
        parse_rubric_schema(payload)


def test_rubric_schema_to_judge_criteria_returns_judge_ready_dicts() -> None:
    rubric = parse_rubric_schema(make_valid_rubric_payload())

    criteria = rubric_schema_to_judge_criteria(rubric)

    assert criteria == [
        {
            "name": "correctness",
            "description": "The response should be factually correct.",
            "min_score": 1.0,
            "max_score": 5.0,
            "weight": 0.4,
        },
        {
            "name": "relevance",
            "description": "The response should directly answer the prompt.",
            "min_score": 1.0,
            "max_score": 5.0,
            "weight": 0.3,
        },
        {
            "name": "clarity",
            "description": "The response should be easy to understand.",
            "min_score": 1.0,
            "max_score": 5.0,
            "weight": 0.3,
        },
    ]


def test_rubric_schema_json_schema_contains_expected_properties() -> None:
    schema = rubric_schema_json_schema()

    assert schema["title"] == "RubricSchema"
    assert "properties" in schema
    assert "rubric_id" in schema["properties"]
    assert "criteria" in schema["properties"]


def test_load_rubric_schema_yaml_loads_the_default_rubric() -> None:
    rubric = load_rubric_schema_yaml()

    assert rubric.rubric_id == "instruction-quality-v0"
    assert rubric.version == "0.1"
    assert {c.name for c in rubric.criteria} == {
        "correctness", "relevance", "completeness", "clarity", "safety",
    }
    assert abs(sum(c.weight for c in rubric.criteria) - 1.0) < 1e-9

def test_load_rubric_schema_yaml_loads_a_custom_file(tmp_path: Path) -> None:
    path = tmp_path / "custom.yaml"
    path.write_text(
        """
rubric_id: custom-rubric
version: "1.0"
description: A custom test rubric.
criteria:
  quality:
    description: Overall quality.
    weight: 1.0
    min_score: 0
    max_score: 10
""".strip(),
        encoding="utf-8",
    )

    rubric = load_rubric_schema_yaml(path)

    assert rubric.rubric_id == "custom-rubric"
    assert [c.name for c in rubric.criteria] == ["quality"]


def test_load_rubric_schema_yaml_rejects_non_mapping_file(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("- just\n- a\n- list\n", encoding="utf-8")

    with pytest.raises(ValueError, match="mapping"):
        load_rubric_schema_yaml(path)


def test_load_rubric_schema_yaml_rejects_missing_criteria(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("rubric_id: x\nversion: '1.0'\ndescription: d\n", encoding="utf-8")

    with pytest.raises(ValueError, match="criteria"):
        load_rubric_schema_yaml(path)