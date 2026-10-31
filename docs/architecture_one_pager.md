# Architecture and API boundaries

Status: implemented offline pipeline, with production extensions identified below.

`app/main.py` registers `/v1/evaluations`. The route validates an
`evaluation.contracts.EvaluationRequest`, calls the service, and returns computed
results plus Markdown. The service adds run-scoped operational log events.
`evaluation/pipeline.py` owns calculation and imports no FastAPI components.
The CLI calls that same pipeline and then the local artifact writer.

## Contracts

- Examples supply IDs, prompts, non-empty references, and one named slice each.
- Separate baseline/challenger output lists are joined by ID, never by position.
- Duplicate, missing, extra, or blank IDs are rejected. Output order is canonical.
- This reference-based workflow rejects missing references rather than inventing scores.
- Input/model identities and settings are validated; unknown fields are rejected.
- Maximum 100 examples, 256 whitespace tokens per reference/response, and 10000
  bootstrap draws support local demo workloads. ROUGE-L uses quadratic LCS memory.
- The API performs no model calls and writes no run artifacts. The CLI owns file writes.

## Components

| Component | Responsibility |
|---|---|
| `contracts.py` | Shared validated request/configuration models |
| `pipeline.py` | Quality checks, metric calculation, slice analysis, retrieval, review decision |
| `statistics.py` | Canonical percentile bootstrap implementation |
| `semantic.py` | Versioned manual synonym-count encoder |
| `comparison_report.py` | Format computed results without hard-coded metrics |
| `artifacts.py` | Hashes, local run directories, manifests, integrity checks |
| `judge_parser.py` | Validate structured judge output; optionally enforce rubric and ID |
| `search_index.py` | Exact ID and metadata lookup, unranked substring keyword search, and BM25-ranked search |
| `retrieval_metrics.py` | precision@k/recall@k/hit@k/MRR/nDCG@k and paired retriever comparison, on top of `statistics.py` |
| `failure_taxonomy.py` | Validates and aggregates failure tags against a shared vocabulary |
| `anomaly_detection.py` | Robust (median/MAD) statistical outlier flags over metrics and response length |
| `significance.py` | Reusable practical-vs-statistical classification, on top of `statistics.py` |
| `text_metrics.py` | ROUGE-L, unigram precision, token recall, cosine similarity, exact-match accuracy |
| `ab_testing.py` | Independent-group two-proportion z-test, rate-difference interval, ship/hold rule |
| `model_comparison.py` | Report-ready paired comparison and latency/batch-size helpers |
| `data_quality.py` | Blocking and warning-level input checks |
| `metrics_summary.py` | Per-metric means and slice counts |
| `rubric_schema.py` | Pydantic-validated rubric loading and weighted scoring |
| `llm_judge.py` | Deterministic judge prompt construction; no live model call |
| `judge_calibration.py` | Agreement, Cohen's kappa, MAE, correlation and calibration gate |
| `tag_trie.py` | Prefix lookup over failure-tag names |

## Proposed production extensions

A worker queue, cancellation, authenticated run retrieval, database transactions,
rate limiting, external-provider adapters, and multi-process resource controls
are design work, not implemented infrastructure.