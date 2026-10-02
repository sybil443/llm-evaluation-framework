"""Validate judge JSON structurally and, when supplied, against the rubric."""
import json
import math
from typing import Any

from evaluation.rubric_schema import RubricSchema, calculate_weighted_score

class JudgeParseError(ValueError):
    pass

def _number(value):
    return type(value) in (int, float) and math.isfinite(value)

def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise JudgeParseError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result

def parse_judge_output(raw_output: str, *, expected_example_id: str | None = None,
                       rubric: RubricSchema | None = None) -> dict[str, Any]:
    try:
        payload = json.loads(raw_output, object_pairs_hook=_object)
    except (json.JSONDecodeError, TypeError) as exc:
        raise JudgeParseError("Judge output is not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise JudgeParseError("Judge output must be a JSON object.")
    required = {"example_id", "overall_score", "criterion_scores"}
    if required - payload.keys():
        raise JudgeParseError("Judge output is missing required fields.")
    if payload.keys() - required - {"failure_tags"}:
        raise JudgeParseError("Judge output contains unknown fields.")
    if not isinstance(payload["example_id"], str) or not payload["example_id"].strip():
        raise JudgeParseError("example_id must be non-empty text.")
    if expected_example_id is not None and payload["example_id"] != expected_example_id:
        raise JudgeParseError("Judge output example_id does not match the requested example.")
    if not _number(payload["overall_score"]) or not 0 <= payload["overall_score"] <= 1:
        raise JudgeParseError("overall_score must be finite and between 0 and 1.")
    rows = payload["criterion_scores"]
    if not isinstance(rows, list):
        raise JudgeParseError("criterion_scores must be a list.")
    if not rows:
        raise JudgeParseError("criterion_scores must be non-empty.")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"criterion", "score", "rationale"}:
            raise JudgeParseError("Each criterion needs criterion, score, and rationale.")
        if any(not isinstance(row[key], str) or not row[key].strip()
               for key in ("criterion", "rationale")):
            raise JudgeParseError("Criterion names and rationales must be non-empty text.")
        if row["criterion"] in seen:
            raise JudgeParseError("Duplicate criterion name.")
        seen.add(row["criterion"])
        if not _number(row["score"]):
            raise JudgeParseError("Criterion scores must be finite numbers.")
    tags = payload.get("failure_tags", [])
    if not isinstance(tags, list) or any(not isinstance(t, str) or not t.strip() for t in tags):
        raise JudgeParseError("failure_tags must be a list of non-empty strings.")
    if rubric is not None:
        criteria = {c.name: c for c in rubric.criteria}
        if seen != set(criteria):
            raise JudgeParseError("Missing or unknown rubric criteria.")
        for row in rows:
            criterion = criteria[row["criterion"]]
            if not criterion.min_score <= row["score"] <= criterion.max_score:
                raise JudgeParseError("Criterion score is outside the rubric range.")
        # Caller receives the rubric-derived score, never an untrusted judge total.
        payload["overall_score"] = calculate_weighted_score(
            rubric, {row["criterion"]: row["score"] for row in rows})
    return payload