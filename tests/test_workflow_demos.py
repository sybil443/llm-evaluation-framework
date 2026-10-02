"""Smoke tests for the standalone workflow demos saved in workflow_demos.json.

These check that each demo runs end to end, is deterministic, and produces
output that the run writer can serialize (canonical_json forbids NaN/inf).
Detailed behaviour is covered by each module's own unit tests.
"""
import pytest

from evaluation.pipeline import canonical_json
from evaluation.significance import SignificanceVerdict
from examples.demo_data import make_demo_request
from examples.failure_analysis_demo import run_failure_analysis_demo
from examples.retrieval_eval_demo import run_retrieval_demo
from examples.retrieval_fixture import DOCUMENTS, QUERIES
from examples.significance_demo import run_significance_demo

VERDICTS = {verdict.value for verdict in SignificanceVerdict}


@pytest.mark.parametrize(
    "demo", [run_retrieval_demo, run_failure_analysis_demo, run_significance_demo]
)
def test_demo_is_deterministic_serializable_and_labelled_synthetic(demo) -> None:
    first = demo()

    assert first["data_kind"] == "synthetic"
    assert first["limitations"]
    assert canonical_json(first) == canonical_json(demo())


def test_retrieval_demo_scores_both_retrievers_on_every_query() -> None:
    result = run_retrieval_demo()

    assert result["corpus_size"] == len(DOCUMENTS)
    assert result["n_queries"] == len(QUERIES)
    for side in ("baseline", "challenger"):
        assert set(result[side]["per_query"]) == set(QUERIES)
    assert result["paired_differences"]


def test_failure_analysis_demo_covers_every_pipeline_row() -> None:
    result = run_failure_analysis_demo()
    taxonomy = result["failure_taxonomy"]

    assert result["n_rows"] == len(make_demo_request().examples)
    assert taxonomy["total_rows"] == result["n_rows"]
    # Every tag the pipeline assigns is registered in the taxonomy file.
    assert taxonomy["unknown_tags"] == []
    for anomaly in result["anomalous_outputs"]["anomalies"]:
        assert anomaly["signal"] in result["anomalous_outputs"]["signals"]


def test_significance_demo_classifies_text_and_retrieval_comparisons() -> None:
    result = run_significance_demo()
    text = result["text_metric_significance"]

    assert text["overall"]["verdict"] in VERDICTS
    assert {row["name"] for row in text["slices"]} == {
        example.slice for example in make_demo_request().examples
    }
    assert all(row["verdict"] in VERDICTS for row in text["slices"])
    assert result["retrieval_significance"]["metrics"]
    assert all(row["verdict"] in VERDICTS for row in result["retrieval_significance"]["metrics"])