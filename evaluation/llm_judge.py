from dataclasses import dataclass
import json
from typing import Any

from evaluation.judge_parser import parse_judge_output


@dataclass(frozen=True)
class JudgeCriterion:
    name: str
    description: str
    min_score: float = 1.0
    max_score: float = 5.0


@dataclass(frozen=True)
class JudgeInput:
    example_id: str
    prompt: str
    candidate_response: str
    reference_response: str | None
    criteria: list[JudgeCriterion]


def build_judge_prompt(judge_input: JudgeInput) -> str:
    """
    Build a deterministic LLM-as-a-Judge prompt.

    This prepares the text that would be sent to a judge model.
    The actual LLM call is intentionally not implemented here.
    """
    if not judge_input.example_id.strip():
        raise ValueError("example_id must be non-empty.")

    if not judge_input.prompt.strip():
        raise ValueError("prompt must be non-empty.")

    if not judge_input.candidate_response.strip():
        raise ValueError("candidate_response must be non-empty.")

    if not judge_input.criteria:
        raise ValueError("At least one judge criterion is required.")

    criteria_text = "\n".join(
        (
            f"- {criterion.name}: {criterion.description} "
            f"(score {criterion.min_score} to {criterion.max_score})"
        )
        for criterion in judge_input.criteria
    )

    reference_text = (
        judge_input.reference_response
        if judge_input.reference_response is not None
        else "No reference response provided."
    )

    return f"""You are an evaluation judge.

Evaluate the candidate response against the prompt, reference response, and rubric criteria.

Return only valid JSON with this schema:
{{
  "example_id": "string",
  "overall_score": number,
  "criterion_scores": [
    {{
      "criterion": "string",
      "score": number,
      "rationale": "string"
    }}
  ],
  "failure_tags": ["string"]
}}

Example ID:
{judge_input.example_id}

Prompt:
{judge_input.prompt}

Reference response:
{reference_text}

Candidate response:
{judge_input.candidate_response}

Rubric criteria:
{criteria_text}
"""


def build_placeholder_judge_output(judge_input: JudgeInput) -> str:
    """
    Build a deterministic placeholder judge output for scaffold testing.

    This lets the framework test prompt construction and parsing before
    integrating a real judge model.
    """
    criterion_scores = [
        {
            "criterion": criterion.name,
            "score": criterion.max_score,
            "rationale": "Placeholder score for scaffold validation.",
        }
        for criterion in judge_input.criteria
    ]

    payload: dict[str, Any] = {
        "example_id": judge_input.example_id,
        "overall_score": 1.0,
        "criterion_scores": criterion_scores,
        "failure_tags": [],
    }

    return json.dumps(payload)


def run_placeholder_judge(judge_input: JudgeInput) -> dict[str, Any]:
    """
    Run the scaffolded judge flow without calling an external LLM.

    Flow:
    JudgeInput -> placeholder JSON output -> parser validation
    """
    raw_output = build_placeholder_judge_output(judge_input)
    return parse_judge_output(raw_output)