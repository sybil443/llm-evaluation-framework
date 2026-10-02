"""HTTP contracts reuse evaluation contracts; evaluation never imports app."""
from pydantic import BaseModel, Field
from evaluation.contracts import EvaluationConfig, EvaluationExample, EvaluationRequest, ModelOutput


class EchoRequest(BaseModel):
    message: str = Field(max_length=4000)


class EchoResponse(BaseModel):
    message: str


class EvaluationResponse(BaseModel):
    result: dict
    report_markdown: str