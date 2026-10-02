import pytest

from evaluation.retrieval_metrics import (
    RetrievalComparison,
    RetrievalReport,
    compare_retrievers,
    evaluate_retrieval,
    hit_at_k,
    ndcg_at_k,
    precision_at_k,
    reciprocal_rank,
    recall_at_k,
    score_query,
)

RANKED = ["d1", "d2", "d3", "d4", "d5"]
RELEVANT = ["d2", "d4"]
RELEVANCE = {"d2": 3, "d4": 1}


def test_precision_at_k_counts_relevant_in_top_k() -> None:
    assert precision_at_k(RANKED, RELEVANT, 3) == pytest.approx(1 / 3)


def test_precision_at_k_with_k_larger_than_ranking() -> None:
    assert precision_at_k(RANKED, RELEVANT, 10) == pytest.approx(2 / 5)


def test_recall_at_k_counts_fraction_of_relevant_found() -> None:
    assert recall_at_k(RANKED, RELEVANT, 3) == 0.5
    assert recall_at_k(RANKED, RELEVANT, 10) == 1.0


def test_hit_at_k_is_binary() -> None:
    assert hit_at_k(RANKED, RELEVANT, 1) == 0.0
    assert hit_at_k(RANKED, RELEVANT, 2) == 1.0


def test_reciprocal_rank_uses_first_relevant_position() -> None:
    assert reciprocal_rank(RANKED, RELEVANT) == 0.5


def test_reciprocal_rank_is_zero_when_nothing_relevant_found_within_k() -> None:
    assert reciprocal_rank(RANKED, RELEVANT, k=1) == 0.0


def test_reciprocal_rank_is_zero_when_relevant_ids_absent_from_ranking() -> None:
    assert reciprocal_rank(["d1", "d3"], ["d9"]) == 0.0


def test_ndcg_at_k_matches_hand_computed_value() -> None:
    import math

    dcg = 3 / math.log2(3) + 1 / math.log2(5)
    idcg = 3 / math.log2(2) + 1 / math.log2(3)

    assert ndcg_at_k(RANKED, RELEVANCE, 5) == pytest.approx(dcg / idcg)


def test_ndcg_at_k_is_one_for_perfect_ranking() -> None:
    ranking = ["d2", "d4", "d1", "d3", "d5"]

    assert ndcg_at_k(ranking, RELEVANCE, 5) == pytest.approx(1.0)


def test_ndcg_at_k_is_zero_when_all_judged_relevance_is_zero() -> None:
    assert ndcg_at_k(RANKED, {"d2": 0, "d4": 0}, 5) == 0.0


def test_precision_at_k_rejects_non_positive_k() -> None:
    with pytest.raises(ValueError, match="k"):
        precision_at_k(RANKED, RELEVANT, 0)


def test_precision_at_k_rejects_duplicate_ranked_ids() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        precision_at_k(["d1", "d1"], RELEVANT, 2)


def test_precision_at_k_rejects_empty_relevant_ids() -> None:
    with pytest.raises(ValueError, match="relevant_ids"):
        precision_at_k(RANKED, [], 3)


def test_ndcg_at_k_rejects_negative_relevance() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        ndcg_at_k(RANKED, {"d2": -1}, 3)


def test_score_query_reports_every_metric_at_every_k() -> None:
    result = score_query(RANKED, RELEVANCE, ks=(1, 3))

    assert set(result) == {
        "mrr",
        "precision_at_1", "recall_at_1", "hit_at_1", "ndcg_at_1",
        "precision_at_3", "recall_at_3", "hit_at_3", "ndcg_at_3",
    }
    assert result["mrr"] == 0.5


def test_score_query_rejects_relevance_with_no_positive_grades() -> None:
    with pytest.raises(ValueError, match="grade > 0"):
        score_query(RANKED, {"d2": 0, "d4": 0})


# --- aggregate report / comparison ---------------------------------------

RANKINGS_A = {"q1": ["d1", "d2", "d3"], "q2": ["d4", "d5", "d6"]}
RANKINGS_B = {"q1": ["d2", "d1", "d3"], "q2": ["d5", "d4", "d6"]}
JUDGMENTS = {"q1": {"d2": 2}, "q2": {"d5": 2}}


def test_evaluate_retrieval_returns_report_with_expected_shape() -> None:
    report = evaluate_retrieval(RANKINGS_A, JUDGMENTS, ks=(1, 3), n_bootstrap=200, seed=1)

    assert isinstance(report, RetrievalReport)
    assert report.n_queries == 2
    assert set(report.per_query) == {"q1", "q2"}
    assert "mrr" in report.summary
    assert report.summary["mrr"]["n"] == 2


def test_evaluate_retrieval_rejects_mismatched_query_ids() -> None:
    with pytest.raises(ValueError, match="same query ids"):
        evaluate_retrieval(RANKINGS_A, {"q1": {"d2": 2}}, n_bootstrap=100)


def test_evaluate_retrieval_rejects_empty_rankings() -> None:
    with pytest.raises(ValueError, match="rankings"):
        evaluate_retrieval({}, {})


def test_compare_retrievers_scores_both_sides_against_same_judgments() -> None:
    comparison = compare_retrievers(
        RANKINGS_A, RANKINGS_B, JUDGMENTS, ks=(1, 3), n_bootstrap=200, seed=1,
    )

    assert isinstance(comparison, RetrievalComparison)
    # d2 is relevant and sits at rank 2 in A's q1 ranking, rank 1 in B's.
    assert comparison.baseline.per_query["q1"]["mrr"] == 0.5
    assert comparison.challenger.per_query["q1"]["mrr"] == 1.0
    assert comparison.differences["mrr"]["mean_difference"] == pytest.approx(0.5)


def test_compare_retrievers_rejects_mismatched_ranking_query_ids() -> None:
    with pytest.raises(ValueError, match="same query ids"):
        compare_retrievers(RANKINGS_A, {"q1": ["d1"]}, JUDGMENTS)


def test_evaluate_retrieval_is_deterministic_for_a_fixed_seed() -> None:
    first = evaluate_retrieval(RANKINGS_A, JUDGMENTS, n_bootstrap=200, seed=7)
    second = evaluate_retrieval(RANKINGS_A, JUDGMENTS, n_bootstrap=200, seed=7)

    assert first.summary == second.summary
