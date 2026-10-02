import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from evaluation.artifacts import save_run, verify_run
from evaluation.comparison_report import render_report
from evaluation.contracts import EvaluationRequest
from evaluation.pipeline import canonical_json, evaluate
from evaluation.semantic import semantic_baseline
from examples.demo_data import make_demo_request
from examples.judge_workflow import run_judge_demo

ROOT = Path(__file__).resolve().parents[1]


def test_aggregate_gain_does_not_hide_slice_regression():
    result = evaluate(make_demo_request())
    assert result["comparison"]["mean_difference"] > 0
    assert result["slices"]["technical"]["mean_difference"] < -0.05
    assert result["decision"]["status"] == "HOLD"
    assert any("technical" in x for x in result["decision"]["reasons"])
    assert any("Synthetic" in x for x in result["decision"]["reasons"])


def test_pairing_and_hashes_are_order_independent():
    request = make_demo_request()
    payload = request.model_dump()
    for key in ("examples", "baseline", "challenger"):
        payload[key].reverse()
    assert evaluate(request) == evaluate(EvaluationRequest.model_validate(payload))


def test_small_dataset_has_no_positive_release_recommendation():
    payload = make_demo_request().model_dump()
    for key in ("examples", "baseline", "challenger"):
        payload[key] = payload[key][:2]
    result = evaluate(EvaluationRequest.model_validate(payload))
    assert result["decision"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert any(x["code"] == "UNDERSIZED_SLICE" for x in result["quality_issues"])


def test_search_retrieves_actual_evaluation_records():
    result = evaluate(make_demo_request())
    assert "ex-001" in result["retrieval_demo"]["keyword_ids"]
    assert "ex-001" not in result["retrieval_demo"]["slice_ids"]["technical"]
    assert "ex-017" in result["retrieval_demo"]["flagged_ids"]


def test_concept_encoder_matches_synonyms_and_exposes_negation_blind_spot():
    score, covered = semantic_baseline("buy a fast car", "purchase a quick automobile")
    assert covered and score == pytest.approx(1)
    # This demonstrates a documented limitation, not a factual correctness test.
    assert semantic_baseline("the backup is safe", "the backup is not safe")[0] == pytest.approx(1)
    assert semantic_baseline("unmapped words", "more unknown words") == (0.0, False)


def test_judge_workflow_calculates_scores_and_passes_gate_with_one_flagged_disagreement():
    result = run_judge_demo()
    assert result["mode"] == "authored_fixture"
    assert result["real_judge_validated"] is False
    assert result["fixture_gate_passed"] is True
    assert result["examples"][1]["parsed_output"]["overall_score"] == pytest.approx(0.0625)
    # judge-5 is the intentional rubric-coverage-gap case (see
    # examples/judge_workflow.py's module docstring): the two-criterion
    # rubric has no safety criterion, so the judge over-scores it relative
    # to the authored "expected" judgment, and the calibration check
    # should still surface that one disagreement even though the overall
    # gate passes.
    assert [d["example_id"] for d in result["calibration"]["disagreements"]] == ["judge-5"]
    assert result["calibration"]["cohens_kappa"] is not None


def test_saved_artifacts_are_traceable_and_cannot_be_overwritten(tmp_path):
    request = make_demo_request()
    result = evaluate(request)
    target = save_run(request, result, render_report(result), tmp_path)
    manifest = verify_run(target)
    assert manifest["request_sha256"] == result["request_sha256"]
    assert "evaluation/pipeline.py" in manifest["source"]["files"]
    with pytest.raises(FileExistsError):
        save_run(request, result, render_report(result), tmp_path)
    (target / "report.md").write_text("tampered")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_run(target)


def test_mismatched_result_cannot_be_saved(tmp_path):
    request = make_demo_request()
    result = evaluate(request)
    result["request_sha256"] = "wrong"
    with pytest.raises(ValueError, match="does not belong"):
        save_run(request, result, render_report(result), tmp_path)


def test_cli_saved_results_match_python_and_report(tmp_path):
    subprocess.run([sys.executable, "-m", "examples.run_llm_eval",
                    "--output", str(tmp_path)], cwd=ROOT, check=True, capture_output=True)
    target = tmp_path / "portfolio-demo-v1"
    result = evaluate(make_demo_request())
    assert (target / "results.json").read_text() == canonical_json(result)
    assert (target / "report.md").read_text() == render_report(result)
    verify_run(target)
    demos = json.loads((target / "workflow_demos.json").read_text())
    assert set(demos) == {"judge_workflow", "independent_ab", "retrieval_evaluation",
                          "failure_analysis", "significance_review"}


def test_committed_report_is_reproducible():
    expected = render_report(evaluate(make_demo_request()))
    assert (ROOT / "examples" / "example_report.md").read_text() == expected