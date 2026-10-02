"""
Retrieval evaluation metrics: precision@k, recall@k, hit@k, MRR, nDCG@k,
and paired retriever comparison built on the same bootstrap primitives the
rest of the evaluation package uses (evaluation.statistics).

Scope and limitations, stated up front:
  - All metrics are computed per query from a ranked list of document IDs
    and a judgment set/mapping for that query, then aggregated by taking
    the mean across queries and bootstrapping a confidence interval on
    that mean. This mirrors how evaluation/pipeline.py aggregates
    per-example text metrics; it is not a specialized IR aggregation
    method (no macro/micro distinction beyond the per-query mean).
  - Relevance judgments are assumed complete and correct for the queries
    evaluated. Nothing here estimates judgment coverage or handles
    partial/pooled judgments.
  - nDCG uses linear (non-exponential) gain and a log2(rank + 1) discount.
    This is one common convention, not the only one; graded relevance
    values are used as-is for gain, so callers choosing a different gain
    function will get different numbers.
  - The paired comparison bootstraps the per-query metric difference and
    is only meaningful when both rankings were evaluated against the same
    queries and judgments, which `compare_retrievers` enforces.
"""
from dataclasses import dataclass, field

from evaluation.statistics import bootstrap_summary, paired_summary

DEFAULT_KS: tuple[int, ...] = (1, 3, 5, 10)


def _check_k(k) -> None:
    if type(k) is not int or k < 1:
        raise ValueError("k must be a positive integer.")


def _check_ks(ks) -> None:
    if len(ks) == 0:
        raise ValueError("ks must not be empty.")
    for k in ks:
        _check_k(k)


def _check_doc_id(doc_id, name="document id") -> None:
    if not isinstance(doc_id, str) or not doc_id.strip():
        raise ValueError(f"{name} must be a non-empty string.")


def _check_ranking(ranked_ids) -> None:
    for doc_id in ranked_ids:
        _check_doc_id(doc_id, "ranked document id")
    if len(set(ranked_ids)) != len(ranked_ids):
        raise ValueError("ranked_ids must not contain duplicate document ids.")


def _check_relevant_ids(relevant_ids) -> None:
    if len(relevant_ids) == 0:
        raise ValueError("relevant_ids must not be empty.")
    for doc_id in relevant_ids:
        _check_doc_id(doc_id, "relevant document id")


def _check_relevance(relevance: dict) -> None:
    if len(relevance) == 0:
        raise ValueError("relevance must not be empty.")
    for doc_id, grade in relevance.items():
        _check_doc_id(doc_id, "relevance document id")
        if isinstance(grade, bool) or not isinstance(grade, (int, float)) or grade < 0:
            raise ValueError(f"relevance grade for {doc_id!r} must be a non-negative number.")


def _check_query_ids(rankings: dict, judgments: dict) -> None:
    if set(rankings) != set(judgments):
        missing_judgments = sorted(set(rankings) - set(judgments))
        missing_rankings = sorted(set(judgments) - set(rankings))
        raise ValueError(
            "rankings and judgments must cover the same query ids. "
            f"Queries missing judgments: {missing_judgments}. "
            f"Queries missing rankings: {missing_rankings}."
        )


def precision_at_k(ranked_ids: list[str], relevant_ids, k: int) -> float:
    """Fraction of the top-k ranked ids that are relevant."""
    _check_k(k)
    _check_ranking(ranked_ids)
    _check_relevant_ids(relevant_ids)
    top_k = ranked_ids[:k]
    if not top_k:
        return 0.0
    relevant = set(relevant_ids)
    return sum(1 for doc_id in top_k if doc_id in relevant) / len(top_k)


def recall_at_k(ranked_ids: list[str], relevant_ids, k: int) -> float:
    """Fraction of all relevant ids retrieved within the top-k."""
    _check_k(k)
    _check_ranking(ranked_ids)
    _check_relevant_ids(relevant_ids)
    relevant = set(relevant_ids)
    top_k = set(ranked_ids[:k])
    return sum(1 for doc_id in relevant if doc_id in top_k) / len(relevant)


def hit_at_k(ranked_ids: list[str], relevant_ids, k: int) -> float:
    """1.0 if any relevant id appears in the top-k, else 0.0."""
    _check_k(k)
    _check_ranking(ranked_ids)
    _check_relevant_ids(relevant_ids)
    relevant = set(relevant_ids)
    return 1.0 if any(doc_id in relevant for doc_id in ranked_ids[:k]) else 0.0


def reciprocal_rank(ranked_ids: list[str], relevant_ids, *, k: int | None = None) -> float:
    """1 / rank of the first relevant id (1-indexed); 0.0 if none found within k (or at all)."""
    if k is not None:
        _check_k(k)
    _check_ranking(ranked_ids)
    _check_relevant_ids(relevant_ids)
    relevant = set(relevant_ids)
    candidates = ranked_ids[:k] if k is not None else ranked_ids
    for rank, doc_id in enumerate(candidates, start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(ranked_ids: list[str], relevance: dict, k: int) -> float:
    """
    Normalized DCG at k with linear gain and log2(rank + 1) discount.

    `relevance` maps document id -> non-negative graded relevance (0
    means not relevant; higher means more relevant). Returns 0.0 when
    every judged document has relevance 0 (ideal DCG is 0), since no
    ranking can do better than an already-zero ideal.
    """
    import math

    _check_k(k)
    _check_ranking(ranked_ids)
    _check_relevance(relevance)
    top_k = ranked_ids[:k]
    dcg = sum(
        relevance.get(doc_id, 0) / math.log2(rank + 1)
        for rank, doc_id in enumerate(top_k, start=1)
    )
    ideal_grades = sorted(relevance.values(), reverse=True)[:k]
    ideal_dcg = sum(
        grade / math.log2(rank + 1) for rank, grade in enumerate(ideal_grades, start=1)
    )
    if ideal_dcg == 0:
        return 0.0
    return dcg / ideal_dcg


def score_query(ranked_ids: list[str], relevance: dict, ks: tuple[int, ...] = DEFAULT_KS) -> dict:
    """
    Compute precision@k, recall@k, hit@k, and nDCG@k for each k in `ks`,
    plus a single MRR value (unbounded by k), for one query.

    `relevance` maps document id -> graded relevance; a document is
    treated as "relevant" for precision/recall/hit/MRR if its grade is
    greater than 0.
    """
    _check_ks(ks)
    _check_relevance(relevance)
    relevant_ids = [doc_id for doc_id, grade in relevance.items() if grade > 0]
    if not relevant_ids:
        raise ValueError("relevance must contain at least one document with grade > 0.")
    result = {"mrr": reciprocal_rank(ranked_ids, relevant_ids)}
    for k in ks:
        result[f"precision_at_{k}"] = precision_at_k(ranked_ids, relevant_ids, k)
        result[f"recall_at_{k}"] = recall_at_k(ranked_ids, relevant_ids, k)
        result[f"hit_at_{k}"] = hit_at_k(ranked_ids, relevant_ids, k)
        result[f"ndcg_at_{k}"] = ndcg_at_k(ranked_ids, relevance, k)
    return result


@dataclass(frozen=True)
class RetrievalReport:
    """Per-metric mean and bootstrap CI, aggregated across queries."""
    metric_names: tuple[str, ...]
    per_query: dict[str, dict[str, float]]
    summary: dict[str, dict[str, float]]
    n_queries: int
    ks: tuple[int, ...] = field(default=DEFAULT_KS)


@dataclass(frozen=True)
class RetrievalComparison:
    """Baseline vs. challenger reports plus a paired bootstrap per metric."""
    baseline: RetrievalReport
    challenger: RetrievalReport
    differences: dict[str, dict[str, float]]


def evaluate_retrieval(
    rankings: dict[str, list[str]],
    judgments: dict[str, dict[str, float]],
    *,
    ks: tuple[int, ...] = DEFAULT_KS,
    n_bootstrap: int = 2000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> RetrievalReport:
    """
    Score every query in `rankings` against its judgments in `judgments`,
    then bootstrap a confidence interval on the mean of each metric.

    `rankings` maps query id -> ranked list of document ids (best first).
    `judgments` maps query id -> {document id: graded relevance}. Both
    dicts must cover exactly the same set of query ids.
    """
    _check_ks(ks)
    if len(rankings) == 0:
        raise ValueError("rankings must not be empty.")
    _check_query_ids(rankings, judgments)
    per_query = {
        query_id: score_query(rankings[query_id], judgments[query_id], ks)
        for query_id in rankings
    }
    metric_names = tuple(next(iter(per_query.values())).keys())
    summary = {
        metric: bootstrap_summary(
            [scores[metric] for scores in per_query.values()],
            n_bootstrap, confidence_level, seed,
        )
        for metric in metric_names
    }
    return RetrievalReport(
        metric_names=metric_names, per_query=per_query, summary=summary,
        n_queries=len(rankings), ks=ks,
    )


def compare_retrievers(
    baseline_rankings: dict[str, list[str]],
    challenger_rankings: dict[str, list[str]],
    judgments: dict[str, dict[str, float]],
    *,
    ks: tuple[int, ...] = DEFAULT_KS,
    n_bootstrap: int = 2000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> RetrievalComparison:
    """
    Evaluate baseline and challenger rankings against the same judgments,
    then bootstrap the paired per-query difference (challenger - baseline)
    for each metric, mirroring evaluation/pipeline.py's `_comparison`.

    Requires `baseline_rankings`, `challenger_rankings`, and `judgments`
    to all cover the same set of query ids, so every difference is a
    true within-query pairing rather than an average-of-averages.
    """
    _check_query_ids(baseline_rankings, challenger_rankings)
    baseline = evaluate_retrieval(
        baseline_rankings, judgments, ks=ks, n_bootstrap=n_bootstrap,
        confidence_level=confidence_level, seed=seed,
    )
    challenger = evaluate_retrieval(
        challenger_rankings, judgments, ks=ks, n_bootstrap=n_bootstrap,
        confidence_level=confidence_level, seed=seed,
    )
    query_ids = list(baseline_rankings)
    differences = {
        metric: paired_summary(
            [baseline.per_query[q][metric] for q in query_ids],
            [challenger.per_query[q][metric] for q in query_ids],
            n_bootstrap, confidence_level, seed,
        )
        for metric in baseline.metric_names
    }
    return RetrievalComparison(baseline=baseline, challenger=challenger, differences=differences)
