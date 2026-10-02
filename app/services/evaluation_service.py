import json
import logging
from time import perf_counter

from evaluation.contracts import EvaluationRequest
from evaluation.pipeline import evaluate

logger = logging.getLogger(__name__)


class EvaluationServiceError(ValueError):
    """An evaluation passed schema validation but cannot be processed."""


def run_evaluation(request: EvaluationRequest) -> dict:
    start = perf_counter()
    logger.info(json.dumps({"event": "evaluation_started", "run_id": request.run_id,
                            "example_count": len(request.examples)}))
    try:
        result = evaluate(request)
    except ValueError as exc:
        logger.warning(json.dumps({"event": "evaluation_failed", "run_id": request.run_id,
                                   "error_type": type(exc).__name__}))
        raise EvaluationServiceError(str(exc)) from exc
    logger.info(json.dumps({"event": "evaluation_completed", "run_id": request.run_id,
                            "duration_ms": round((perf_counter() - start) * 1000, 2),
                            "quality_issue_count": len(result["quality_issues"]),
                            "decision": result["decision"]["status"]}))
    return result

