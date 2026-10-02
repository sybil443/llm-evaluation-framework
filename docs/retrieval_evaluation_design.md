# Retrieval evaluation: design and limitations

Status: implemented and tested against an authored fixture; not run against a
real corpus, real queries, or real user relevance judgments.

## What this adds

| Component | File | Purpose |
|---|---|---|
| BM25 ranking | `evaluation/search_index.py` (`InMemorySearchIndex.search`) | Ranks items against a query instead of returning an unordered match set |
| Retrieval metrics | `evaluation/retrieval_metrics.py` | precision@k, recall@k, hit@k, MRR, nDCG@k, per-query aggregation with bootstrap CIs, paired retriever comparison |
| Fixture corpus | `examples/retrieval_fixture.py` | Fourteen authored documents, five queries, hand-authored relevance grades |
| Runnable demo | `examples/retrieval_eval_demo.py` | Builds the index, ranks with two retrievers, scores, compares, returns a JSON-serializable result |
| Wiring | `examples/run_llm_eval.py` | `run_retrieval_demo()` output is saved under `workflow_demos.json` alongside the judge and A/B demos |

The pre-existing `search_by_keyword` and `search_by_metadata` methods are
unchanged; every existing test for them still passes. `search` is additive.

## Why BM25, and why not compared against `search_by_keyword` directly

`search_by_keyword` does a case-insensitive substring match of the *entire*
normalized query against each document's text. It was designed as a simple
exact-match filter, not a ranker, and it has no way to score partial term
overlap. Using it as the "baseline" in a ranking comparison would be a
strawman: it returns an empty result for every multi-word query in the
fixture corpus, because none of the documents happen to contain the query as
a literal substring. `examples/retrieval_eval_demo.py` still runs it and
reports the (empty) results under `substring_search_before`, purely as
descriptive context for what the pre-existing capability could and could not
do.

The quantitative comparison instead pits BM25 against `term_overlap_rankings`
(defined in `examples/retrieval_fixture.py`): a naive but real ranking
baseline that scores documents by raw query-term overlap count, with no IDF
weighting and no document-length normalization. This is the kind of ranking
a keyword-count approach reaches for before adopting BM25, so the comparison
demonstrates what BM25's weighting actually buys, rather than comparing a
ranker to a method that structurally cannot rank multi-word queries.

## Metric definitions

| Metric | Definition | Limitation |
|---|---|---|
| `precision_at_k` | Fraction of the top-k ranked ids that are relevant | Ignores rank position within the top-k |
| `recall_at_k` | Fraction of all relevant ids found within the top-k | Needs a complete relevant-id set; undercounts if judgments are incomplete |
| `hit_at_k` | 1.0 if any relevant id appears in the top-k, else 0.0 | Binary; doesn't distinguish one hit from several |
| `reciprocal_rank` (MRR when averaged) | 1 / rank of the first relevant id | Only rewards the first relevant hit; ignores everything after it |
| `ndcg_at_k` | DCG (linear gain, log2(rank+1) discount) normalized by ideal DCG | One gain/discount convention among several; graded relevance is used as-is |

Tokenization for BM25 (`search_tokens`) lowercases and splits on non-alphanumeric
characters — the same convention used elsewhere in this repo's lexical metrics.

## Aggregation and the paired comparison

Per-query scores are aggregated by taking the mean across queries and
bootstrapping a confidence interval on that mean, using the same
`evaluation.statistics.bootstrap_summary` and `paired_summary` functions the
rest of the evaluation pipeline uses for text-metric comparisons
(`evaluation/pipeline.py`). `compare_retrievers` requires the baseline and
challenger rankings and the judgments to all cover the same query ids, so
every paired difference is a true within-query pairing, not an
average-of-averages.

## Fixture results (authored corpus, not a benchmark)

Running `examples/retrieval_eval_demo.py` against the fourteen-document
fixture and five authored queries shows a small, real improvement from BM25
over the naive term-overlap baseline, e.g. (seed 42, defaults):

| Metric | term_overlap (baseline) | BM25 (challenger) |
|---|---|---|
| precision@3 | 0.733 | 0.800 |
| recall@3 | 0.833 | 0.900 |
| nDCG@3 | 0.916 | 0.945 |

These numbers describe this fixture only. With five queries the bootstrap
intervals are wide; the demo output includes them (`paired_differences`),
and they should not be read as a precise, generalizable effect size.

## Limitations

- Fourteen authored documents and five authored queries. This is a
  correctness and workflow demonstration, not an information-retrieval
  benchmark, and the numbers above do not generalize beyond the fixture.
- Relevance grades were authored by hand against the corpus text, not
  collected from independent judges, click data, or any labeling process.
- One judgment (`q-recover-account` / `doc-pwd-forgot`) shares no vocabulary
  with its query by design. No lexical ranker implemented here — BM25 or
  term-overlap — can retrieve it. This is included deliberately to document
  a real limitation of lexical retrieval (vocabulary/synonym mismatch), the
  same limitation already called out for the concept-cosine semantic
  baseline in `docs/lexical_vs_semantic_metrics_design.md`.
- BM25 and term-overlap are both purely lexical: neither captures synonymy,
  paraphrase, or word order. Pairing this retrieval layer with the
  concept-cosine baseline (or a real embedding model) is future work, not
  implemented here.
- `evaluate_retrieval` and `compare_retrievers` assume the provided relevance
  judgments are complete for the queries evaluated; nothing here estimates
  judgment coverage or supports pooled/partial judgments (a standard
  simplification for a from-scratch evaluation harness, not a claim of
  exhaustive judging).
- The bootstrap assumes independent queries, matching the same assumption
  the rest of the pipeline makes about independent example pairs; clustered
  or dependent queries would need cluster resampling.
- No live index or search service is exercised; `InMemorySearchIndex` holds
  everything in memory and rebuilds its BM25 statistics (term counts,
  document frequency, average length) lazily and in full whenever an item is
  added, which is appropriate for the corpus sizes used here (tests, demos,
  offline evaluation) and not benchmarked at production index scale.
