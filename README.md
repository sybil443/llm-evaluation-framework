# LLM / Model Evaluation Framework

A modular Python toolkit and FastAPI service for comparing supplied baseline and
challenger responses. The same pipeline runs through HTTP and the command line.
It calculates lexical metrics, a small semantic similarity baseline, paired
bootstrap intervals, slice summaries, review flags, and a Markdown report.

**Status:** working offline portfolio prototype. The included 24 examples are
explicitly authored synthetic fixtures, not real model outputs or an empirical
benchmark. No LLM provider, hosted service, or pretrained embedding model is used.

## Quick start

Use Python **3.12**. From the repository root (macOS/Linux):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m examples.run_llm_eval
```

Open `runs/portfolio-demo-v1/report.md`. A repeated run ID is rejected to prevent
silent overwrites; use `--output runs-repeat` to create another run elsewhere.

The [committed report](examples/example_report.md) is generated from the same
pipeline, not manually entered numbers. Regenerate it with:

```bash
python -m examples.generate_example_report
```

The demo returns **HOLD**: the aggregate primary metric improves, but its interval
includes zero and the technical slice regresses. Synthetic data also block any
claim of real model superiority. This is a demonstration of evaluation controls.

## API

```bash
python -m uvicorn app.main:app --reload
```

Open [local Swagger UI](http://127.0.0.1:8000/docs). In another terminal:

```bash
python -m examples.demo_data > /tmp/evaluation-request.json
curl -sS http://127.0.0.1:8000/v1/evaluations \
  -H 'Content-Type: application/json' \
  --data-binary @/tmp/evaluation-request.json
```

`POST /v1/evaluations` returns `result` and `report_markdown`. It computes actual
metrics and does not save files. The CLI saves local artifacts. `/health`,
`/hello`, and `/echo` remain available.

**Contract migration:** the earlier placeholder request is replaced. Requests
now contain `dataset_name`, `dataset_version`, `data_kind`, `provenance`,
`baseline_name`, `challenger_name`, `examples`, `baseline`, `challenger`, and
`config`. Each example has a required reference and slice. Both output lists
must contain exactly those example IDs. Settings such as `seed` live in `config`.
The old `judge_name`, `rubric_version`, and placeholder score fields are removed.

## Implemented capabilities

| Capability | Evidence |
|---|---|
| Shared API/CLI pipeline | `evaluation/pipeline.py`, `tests/test_api.py`, `tests/test_pipeline.py` |
| Input quality and ID pairing | `evaluation/contracts.py`, `evaluation/data_quality.py` |
| Lexical metrics | Unigram precision, ROUGE-L F1, token recall in `evaluation/text_metrics.py` |
| Semantic baseline | `evaluation/semantic.py`: cosine over manually defined synonym-count vectors |
| Paired comparison | One canonical bootstrap in `evaluation/statistics.py` |
| Independent-group A/B utility | `examples/ab_demo.py`; illustrative counts, not an online experiment |
| Metrics and slice summaries | `evaluation/metrics_summary.py`, `evaluation/pipeline.py` |
| Failure review and retrieval | Keyword / metadata search over actual evaluation records |
| Judge workflow design | `examples/judge_workflow.py`: prompt, fixture JSON, strict parsing, rubric-derived score, calibration |
| Local reproducibility | Input/config hashes, source fingerprint, dependency versions, per-example results, reports |
| Automated verification | Unit and integration tests, offline demo, committed-report check, GitHub Actions |

The semantic baseline maps a few synonyms to the same vector dimensions; it is
not a pretrained sentence embedding or a factuality metric. Judge calibration
uses authored fixtures and is **not evidence that a real judge is calibrated**.

## Results and reproducibility

The CLI writes `request.json`, `results.json`, `report.md`, `workflow_demos.json`,
and `manifest.json`. The manifest records artifact hashes, source hashes,
runtime versions, timestamp, and completion status. Deterministic results exclude
timestamps. Re-running identical inputs with the same source and pinned runtime
reproduces scores and report bytes; manifests intentionally have new timestamps.

To evaluate supplied outputs:

```bash
python -m examples.run_llm_eval \
  --input path/to/request.json --output runs-custom
```

Use `data_kind: recorded` only for actual recorded responses with truthful
provenance. This flag does not prove independence or dataset representativeness.

## Evaluation decisions

ROUGE-L F1 is the predefined primary metric, not a combined quality score.
The pipeline uses sample minima, paired uncertainty, an observed-effect threshold,
and slice regression guardrails. It returns `INSUFFICIENT_EVIDENCE`, `HOLD`, or
`REVIEW_CANDIDATE`. Even `REVIEW_CANDIDATE` requires human quality, safety, and
operational review. Thresholds are demo policies, not statistically derived power
requirements. Slice intervals are exploratory, with no multiplicity adjustment.

## Architecture and design

The dependency direction is `app -> evaluation`; the evaluation package never
imports FastAPI. `examples/` supplies fixtures and orchestration for demonstrations.

- [Architecture and API boundaries](docs/architecture_one_pager.md)
- [Metrics and semantic limitations](docs/lexical_vs_semantic_metrics_design.md)
- [Statistical methodology](docs/practical_vs_statistical_significance_design.md)
- [Judge workflow and calibration](docs/judge_calibration_workflow.md)
- [Persistence and traceability](docs/persistence_state_handling_design.md)
- [Errors and reliability](docs/error_handling_service_reliability_note.md)
- [Monitoring and model lifecycle design](docs/monitoring_and_lifecycle.md)
- [Deployment readiness](docs/deployment_readiness_checklist.md)

## Current limits

Local synchronous prototype: no authentication, hosted deployment, live judge,
job queue, database, live drift detection, or online experimentation platform.
Input limits bound this small demonstration; they are not full production resource
controls. Do not expose the development server publicly. See the deployment design
for the separate production requirements.

The author has not selected an open-source license; see the publishing checklist.