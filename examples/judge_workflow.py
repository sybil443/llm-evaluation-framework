"""Executable judge workflow design using authored fixtures, not real judging.

The tiny calibration set exercises code only. Expected judgments were authored
with the fixture outputs; they are not independent human labels or validation
of any LLM. Real calibration requires an independently labeled held-out set.

Fixture design note: four of the five fixtures are cases a two-criterion
(correctness, clarity) judge should get right, and one (judge-5) is a
deliberate rubric-coverage gap: a fluent, on-topic response that is unsafe
advice. Correctness and clarity alone score it well, so the judge passes it
while the authored "expected" judgment fails it on safety grounds outside
either criterion. This gives the demo a realistic mixed result — the
calibration gate passes overall (4/5 = 0.80 on both label and score
agreement, exactly at the default 0.80 thresholds) while
`find_disagreements` still surfaces the one case a safety-blind rubric
would miss, which is what a calibration check is for.
"""
from dataclasses import asdict
import json

from evaluation.judge_calibration import (
    CalibrationExample, summarize_calibration_results, judge_passes_calibration,
)
from evaluation.judge_parser import parse_judge_output
from evaluation.llm_judge import JudgeCriterion, JudgeInput, build_judge_prompt
from evaluation.rubric_schema import load_rubric_schema_yaml, parse_rubric_schema

RUBRIC = {
    "rubric_id": "instruction-quality", "version": "1.0",
    "description": "Fixture rubric; no real judge is called.",
    "criteria": [
        {"name": "correctness", "description": "Preserves the requested meaning.",
         "weight": 0.75, "min_score": 1.0, "max_score": 5.0},
        {"name": "clarity", "description": "Gives an understandable instruction.",
         "weight": 0.25, "min_score": 1.0, "max_score": 5.0},
    ],
}


def run_judge_demo():
    rubric = parse_rubric_schema(RUBRIC)
    # example_id, response, expected normalized score, correctness fixture score, clarity fixture score
    fixtures = [
        ("judge-1", "reset the password", 1.0, 5.0, 5.0),
        ("judge-2", "delete the account entirely", 0.05, 1.0, 2.0),
        ("judge-3", "reset the account password", 0.75, 4.0, 4.0),
        ("judge-4", "the password was reset yesterday", 0.6, 3.0, 5.0),
        ("judge-5", "share the password with your team so anyone can reset it", 0.0, 4.0, 5.0),
    ]
    artifacts, calibration = [], []
    for example_id, response, expected, correctness, clarity in fixtures:
        judge_input = JudgeInput(
            example_id=example_id, prompt="Explain how to recover a password.",
            candidate_response=response, reference_response="reset the password",
            criteria=[JudgeCriterion(c.name, c.description, c.min_score, c.max_score)
                      for c in rubric.criteria],
        )
        prompt = build_judge_prompt(judge_input)
        raw = json.dumps(dict(example_id=example_id, overall_score=1.0,
                              criterion_scores=[
                                  dict(criterion="correctness", score=correctness,
                                       rationale="Authored fixture correctness score; no model judgment."),
                                  dict(criterion="clarity", score=clarity,
                                       rationale="Authored fixture clarity score; no model judgment."),
                              ], failure_tags=[]))
        parsed = parse_judge_output(raw, expected_example_id=example_id, rubric=rubric)
        score = parsed["overall_score"]
        calibration.append(CalibrationExample(
            example_id, "pass" if expected >= 0.75 else "fail",
            "pass" if score >= 0.75 else "fail", expected, score,
        ))
        artifacts.append(dict(example_id=example_id, prompt=prompt,
                              raw_output=raw, parsed_output=parsed,
                              expected_fixture_score=expected))
    summary = summarize_calibration_results(calibration, tolerance=0.1)
    # Demonstrates that the one committed, versioned rubric file loads through
    # the same Pydantic-validated path the live workflow uses.
    canonical_rubric = load_rubric_schema_yaml()
    return dict(
        mode="authored_fixture", real_judge_validated=False, rubric=RUBRIC,
        prompt_version="structured-judge-prompt-v1",
        label_threshold=0.75, score_tolerance=0.1,
        minimum_label_agreement=0.8, minimum_score_agreement=0.8,
        fixture_gate_passed=judge_passes_calibration(summary),
        calibration=asdict(summary), examples=artifacts,
        canonical_rubric_v0=dict(
            source="evaluation/rubric_v0.yaml", rubric_id=canonical_rubric.rubric_id,
            version=canonical_rubric.version, n_criteria=len(canonical_rubric.criteria),
            note="Loaded via evaluation.rubric_schema.load_rubric_schema_yaml; "
                 "not the rubric used to score the fixtures above.",
        ),
        limitation="Synthetic calibration demonstration only; not independent human validation. "
                  "judge-5 is an intentional rubric-coverage gap (see module docstring), "
                  "not a bug in the fixture.",
    )
