from fastapi import APIRouter, HTTPException
from evaluation.comparison_report import render_report
from app.schemas import EvaluationRequest, EvaluationResponse
from app.services.evaluation_service import EvaluationServiceError, run_evaluation

router = APIRouter()


@router.post("/evaluations", response_model=EvaluationResponse, summary="Compare supplied baseline and challenger responses")
def create_evaluation(request: EvaluationRequest) -> dict:
    try:
        result = run_evaluation(request)
    except EvaluationServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"result": result, "report_markdown": render_report(result)}