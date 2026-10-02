import pytest

from evaluation.llm_judge import (
    JudgeCriterion,
    JudgeInput,
    build_judge_prompt,
    build_placeholder_judge_output,
    run_placeholder_judge,
)


def make_judge_input() -> JudgeInput:
    return JudgeInput(
        example_id="ex-001",
        prompt="Summarize the customer complaint.",
        candidate_response="The customer is upset about a delayed claim.",
        reference_response="The customer reported frustration because the claim was delayed.",
        criteria=[
            JudgeCriterion(
                name="correctness",
                description="The response should be factually consistent with the reference.",
            ),
            JudgeCriterion(
                name="relevance",
                description="The response should answer the prompt directly.",
            ),
        ],
    )


def test_build_judge_prompt_contains_required_sections() -> None:
    judge_input = make_judge_input()

    prompt = build_judge_prompt(judge_input)

    assert "Return only valid JSON" in prompt
    assert "Example ID:" in prompt
    assert "Prompt:" in prompt
    assert "Reference response:" in prompt
    assert "Candidate response:" in prompt
    assert "Rubric criteria:" in prompt
    assert "correctness" in prompt
    assert "relevance" in prompt


def test_build_judge_prompt_handles_missing_reference() -> None:
    judge_input = JudgeInput(
        example_id="ex-002",
        prompt="Answer the question.",
        candidate_response="This is an answer.",
        reference_response=None,
        criteria=[
            JudgeCriterion(
                name="clarity",
                description="The response should be easy to understand.",
            )
        ],
    )

    prompt = build_judge_prompt(judge_input)

    assert "No reference response provided." in prompt


def test_build_judge_prompt_rejects_blank_example_id() -> None:
    judge_input = JudgeInput(
        example_id="   ",
        prompt="Prompt",
        candidate_response="Candidate",
        reference_response="Reference",
        criteria=[
            JudgeCriterion(
                name="correctness",
                description="Correctness criterion.",
            )
        ],
    )

    with pytest.raises(ValueError, match="example_id"):
        build_judge_prompt(judge_input)


def test_build_judge_prompt_rejects_empty_criteria() -> None:
    judge_input = JudgeInput(
        example_id="ex-001",
        prompt="Prompt",
        candidate_response="Candidate",
        reference_response="Reference",
        criteria=[],
    )

    with pytest.raises(ValueError, match="criterion"):
        build_judge_prompt(judge_input)


def test_build_placeholder_judge_output_is_parseable_json() -> None:
    judge_input = make_judge_input()

    raw_output = build_placeholder_judge_output(judge_input)

    assert '"example_id": "ex-001"' in raw_output
    assert '"overall_score": 1.0' in raw_output
    assert '"criterion_scores"' in raw_output


def test_run_placeholder_judge_returns_parsed_payload() -> None:
    judge_input = make_judge_input()

    payload = run_placeholder_judge(judge_input)

    assert payload["example_id"] == "ex-001"
    assert payload["overall_score"] == 1.0
    assert len(payload["criterion_scores"]) == 2