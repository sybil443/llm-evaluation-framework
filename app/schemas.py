"""HTTP contracts reuse evaluation contracts; evaluation never imports app."""
from pydantic import BaseModel, Field
from evaluation.contracts import EvaluationConfig, EvaluationExample, EvaluationRequest, ModelOutput

class EvaluationResponse(BaseModel):
    result: dict
    report_markdown: str