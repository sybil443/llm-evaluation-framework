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

Two other bootstrap entry points (`bootstrap_ci.py`, used only by
`ab_compare.py`) and a second report formatter (`report_generator.py`,
which required a `judge_name` field the current contract removed) used to
sit alongside `statistics.py` and `comparison_report.py`, reachable only
from their own tests and not from the API, CLI, or any demo. They were
removed rather than kept as unused duplicates; `statistics.py` is the one
bootstrap implementation and `comparison_report.py` is the one report
formatter actually used end to end.

## Proposed production extensions

A worker queue, cancellation, authenticated run retrieval, database transactions,
rate limiting, external-provider adapters, and multi-process resource controls
are design work, not implemented infrastructure.