"""Executable retrieval evaluation workflow using the authored fixture corpus.

Builds an `InMemorySearchIndex`, ranks the fixture queries with a naive
term-overlap baseline and with BM25, scores both against the authored
relevance judgments, and bootstraps a paired comparison. This is a code
demonstration over a fourteen-document, five-query fixture, not a
validated information-retrieval benchmark.
"""
from dataclasses import asdict

from evaluation.retrieval_metrics import DEFAULT_KS, compare_retrievers
from examples.retrieval_fixture import (
    JUDGMENTS, QUERIES, bm25_rankings, build_index, keyword_rankings, term_overlap_rankings,
)


def run_retrieval_demo():
    index = build_index()
    keyword_before = keyword_rankings(index)
    baseline_rankings = term_overlap_rankings(index)
    challenger_rankings = bm25_rankings(index)
    comparison = compare_retrievers(baseline_rankings, challenger_rankings, JUDGMENTS)
    return dict(
        data_kind="synthetic",
        corpus_size=len(index),
        n_queries=len(QUERIES),
        ks=list(DEFAULT_KS),
        substring_search_before=dict(
            method="search_by_keyword (unranked, exact substring)",
            rankings=keyword_before,
            note="Requires the whole query to appear verbatim in the text; "
                 "returns nothing for every multi-word fixture query. Shown "
                 "for context only, not used in the metric comparison below.",
        ),
        baseline=dict(
            method="term_overlap (naive ranking: raw term-overlap count, no IDF, no length norm)",
            rankings=baseline_rankings,
            per_query=comparison.baseline.per_query,
            summary=comparison.baseline.summary,
        ),
        challenger=dict(
            method="BM25 (evaluation.search_index.InMemorySearchIndex.search)",
            rankings=challenger_rankings,
            per_query=comparison.challenger.per_query,
            summary=comparison.challenger.summary,
        ),
        paired_differences=comparison.differences,
        judgments=JUDGMENTS,
        limitations=[
            "Fourteen authored documents and five authored queries; too small to "
            "generalize a ranking-quality claim beyond this fixture.",
            "Relevance grades were authored by hand against the corpus text, not "
            "collected from independent judges or real user behavior.",
            "One judgment (q-recover-account / doc-pwd-forgot) shares no "
            "vocabulary with its query by design, so no lexical ranker here can "
            "retrieve it; this demonstrates a real vocabulary-mismatch limit of "
            "lexical retrieval, not a fixture defect.",
            "Bootstrap CIs assume independent queries; with five queries the "
            "intervals are wide and mainly illustrate the mechanism, not a "
            "precise effect-size estimate.",
            "BM25 and term-overlap are both lexical methods; neither captures "
            "synonymy or paraphrase, matching the semantic-metric limitations "
            "already documented in evaluation/semantic.py.",
        ],
    )


if __name__ == "__main__":
    import json

    result = run_retrieval_demo()
    print(json.dumps(result, indent=2, sort_keys=True))
