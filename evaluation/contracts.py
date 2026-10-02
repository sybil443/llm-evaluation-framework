"""API-independent input contracts for offline and HTTP evaluation."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Text = Annotated[str, Field(min_length=1, max_length=4000)]
Identifier = Annotated[str, Field(min_length=1, max_length=100)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True,
                              allow_inf_nan=False)


class EvaluationExample(StrictModel):
    example_id: Identifier
    prompt: Text
    reference_response: Text
    slice: Identifier

    @field_validator("reference_response")
    @classmethod
    def limit_tokens(cls, value):
        if len(value.split()) > 256:
            raise ValueError("Reference is limited to 256 whitespace tokens.")
        return value


class ModelOutput(StrictModel):
    example_id: Identifier
    response: Text

    @field_validator("response")
    @classmethod
    def limit_tokens(cls, value):
        if len(value.split()) > 256:
            raise ValueError("Response is limited to 256 whitespace tokens.")
        return value


class EvaluationConfig(StrictModel):
    n_bootstrap: int = Field(default=2000, ge=100, le=10000, strict=True)
    confidence_level: float = Field(default=0.95, gt=0, lt=1)
    seed: int = Field(default=42, ge=0, strict=True)
    minimum_effect: float = Field(default=0.02, ge=0, le=1)
    min_pairs: int = Field(default=20, ge=2, strict=True)
    min_slice_size: int = Field(default=5, ge=2, strict=True)
    max_slice_regression: float = Field(default=0.05, ge=0, le=1)
    low_overlap_threshold: float = Field(default=0.3, ge=0, le=1)


class EvaluationRequest(StrictModel):
    run_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")
    dataset_name: Identifier
    dataset_version: Identifier
    data_kind: Literal["synthetic", "recorded"]
    provenance: Text
    baseline_name: Identifier
    challenger_name: Identifier
    examples: list[EvaluationExample] = Field(min_length=1, max_length=100)
    baseline: list[ModelOutput] = Field(min_length=1, max_length=100)
    challenger: list[ModelOutput] = Field(min_length=1, max_length=100)
    config: EvaluationConfig = Field(default_factory=EvaluationConfig)

    @model_validator(mode="after")
    def validate_pairing(self):
        sets = []
        for label in ("examples", "baseline", "challenger"):
            ids = [item.example_id for item in getattr(self, label)]
            if len(ids) != len(set(ids)):
                raise ValueError(f"Duplicate example_id in {label}.")
            sets.append(set(ids))
        if not sets[0] == sets[1] == sets[2]:
            raise ValueError("examples, baseline, and challenger must have identical IDs.")
        if self.baseline_name == self.challenger_name:
            raise ValueError("Baseline and challenger names must differ.")
        return self