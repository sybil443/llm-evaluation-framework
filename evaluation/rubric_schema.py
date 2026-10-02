import math
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DEFAULT_RUBRIC_YAML_PATH = Path(__file__).with_name("rubric_v0.yaml")


class RubricCriterionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)
    name: str
    description: str
    weight: float
    min_score: float = 1.0
    max_score: float = 5.0

    @field_validator("name", "description")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field must not be blank.")
        return value

    @field_validator("weight")
    @classmethod
    def weight_must_be_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("weight must be positive.")
        return value

    @model_validator(mode="after")
    def score_range_must_be_valid(self) -> "RubricCriterionSchema":
        if self.min_score >= self.max_score:
            raise ValueError("min_score must be less than max_score.")
        return self


class RubricSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)
    rubric_id: str
    version: str
    description: str
    criteria: list[RubricCriterionSchema] = Field(min_length=1)

    @field_validator("rubric_id", "version", "description")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field must not be blank.")
        return value

    @model_validator(mode="after")
    def weights_must_sum_to_one(self) -> "RubricSchema":
        names = [criterion.name for criterion in self.criteria]
        if len(names) != len(set(names)):
            raise ValueError("Rubric criterion names must be unique.")
        total_weight = sum(criterion.weight for criterion in self.criteria)

        if abs(total_weight - 1.0) > 1e-6:
            raise ValueError("Rubric criterion weights must sum to 1.0.")

        return self


def parse_rubric_schema(payload: dict[str, Any]) -> RubricSchema:
    """
    Parse and validate a rubric schema from a dictionary.

    This is intended for JSON-like rubric definitions used by
    LLM-as-a-Judge prompts and evaluation reports.
    """
    return RubricSchema.model_validate(payload)


def load_rubric_schema_yaml(path: str | Path | None = None) -> RubricSchema:
    """
    Load a RubricSchema from a rubric YAML file such as rubric_v0.yaml.

    The file stores `criteria` as a mapping keyed by criterion name (easier
    to read and edit by hand); this adapts it into RubricSchema's
    list-of-criteria shape, then validates it with Pydantic.
    """
    rubric_path = Path(path) if path is not None else DEFAULT_RUBRIC_YAML_PATH
    payload = yaml.safe_load(rubric_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Rubric file must contain a YAML mapping.")
    criteria_payload = payload.get("criteria")
    if not isinstance(criteria_payload, dict) or not criteria_payload:
        raise ValueError("Rubric file must contain a non-empty 'criteria' mapping.")
    criteria = [
        {"name": name, **spec}
        for name, spec in criteria_payload.items()
    ]
    return parse_rubric_schema({
        "rubric_id": payload.get("rubric_id"),
        "version": payload.get("version"),
        "description": payload.get("description"),
        "criteria": criteria,
    })

def calculate_weighted_score(rubric: RubricSchema, scores: dict[str, float]) -> float:
    """
    Combine per-criterion scores into one rubric score in [0, 1].

    Each score is normalized to [0, 1] within its criterion's
    [min_score, max_score] range, then weighted by the criterion weight.
    `scores` must contain exactly the rubric's criteria.
    """
    criteria = {criterion.name: criterion for criterion in rubric.criteria}
    missing = set(criteria) - set(scores)
    if missing:
        raise ValueError(f"Scores are missing required criteria: {sorted(missing)}")
    extra = set(scores) - set(criteria)
    if extra:
        raise ValueError(f"Scores include unknown criteria: {sorted(extra)}")

    weighted_total = 0.0
    for criterion in rubric.criteria:
        score = scores[criterion.name]
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
            raise ValueError(f"Score for '{criterion.name}' must be a finite number.")
        if not criterion.min_score <= score <= criterion.max_score:
            raise ValueError(
                f"Score for '{criterion.name}' must be between "
                f"{criterion.min_score} and {criterion.max_score}, got {score}."
            )
        weighted_total += criterion.weight * (score - criterion.min_score) / (
            criterion.max_score - criterion.min_score
        )
    return weighted_total

def rubric_schema_to_judge_criteria(rubric: RubricSchema) -> list[dict[str, Any]]:
    """
    Convert a validated rubric schema into judge-ready criteria.

    This keeps the judge prompt construction separate from rubric validation.
    """
    return [
        {
            "name": criterion.name,
            "description": criterion.description,
            "min_score": criterion.min_score,
            "max_score": criterion.max_score,
            "weight": criterion.weight,
        }
        for criterion in rubric.criteria
    ]


def rubric_schema_json_schema() -> dict[str, Any]:
    """
    Return the JSON schema for the rubric model.

    This can be used in documentation, prompt scaffolding, or API contracts.
    """
    return RubricSchema.model_json_schema()

