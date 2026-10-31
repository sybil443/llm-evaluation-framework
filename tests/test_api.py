from fastapi.testclient import TestClient
import pytest

from app.main import app
from evaluation.comparison_report import render_report
from evaluation.pipeline import canonical_json, evaluate
from examples.demo_data import make_demo_request

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_api_and_python_produce_identical_computed_results():
    request = make_demo_request()
    expected = evaluate(request)
    response = client.post("/v1/evaluations", json=request.model_dump())
    assert response.status_code == 200
    # JSON canonicalization accounts for in-memory tuples serialized as arrays.
    assert canonical_json(response.json()["result"]) == canonical_json(expected)
    assert response.json()["report_markdown"] == render_report(expected)
    assert response.json()["result"]["comparison"]["mean_difference"] != 1.0


@pytest.mark.parametrize("field", ["run_id", "dataset_name", "baseline_name", "provenance"])
def test_blank_request_identity_is_rejected(field):
    payload = make_demo_request().model_dump()
    payload[field] = "   "
    assert client.post("/v1/evaluations", json=payload).status_code == 422


def test_duplicate_and_missing_pair_ids_are_rejected():
    for change in ("duplicate", "missing"):
        payload = make_demo_request().model_dump()
        if change == "duplicate":
            payload["baseline"][1]["example_id"] = payload["baseline"][0]["example_id"]
        else:
            payload["challenger"].pop()
        assert client.post("/v1/evaluations", json=payload).status_code == 422


def test_api_scores_change_when_challenger_changes():
    payload = make_demo_request().model_dump()
    for record in payload["challenger"]:
        record["response"] = "irrelevant gibberish"
    response = client.post("/v1/evaluations", json=payload)
    assert response.status_code == 200
    assert response.json()["result"]["metric_means"]["challenger"]["rouge_l_f1"] == 0
    assert response.json()["result"]["decision"]["status"] == "HOLD"