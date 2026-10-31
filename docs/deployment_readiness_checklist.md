# Deployment Readiness Checklist

## Purpose

This checklist defines what needs to be true before the LLM evaluation framework is considered ready for a production-like deployment.

The goal is not to claim that the current project is fully production deployed. The goal is to document the readiness criteria, the current status of each one, known gaps, and next engineering steps needed to move from a local FastAPI evaluation project toward a more reliable ML evaluation service.

Status key: ✅ done · ⚠️ partial · ❌ not yet · ➖ not applicable at this stage

---

## 1. Application readiness

| Check                                      | Status | Notes                                                                 |
| ------------------------------------------ | ------ | --------------------------------------------------------------------- |
| FastAPI app starts locally                 | ✅     | `python -m uvicorn app.main:app --reload`; exercised by `TestClient` in `tests/test_api.py` |
| Health endpoint exists                     | ✅     | `/health`; tested in `tests/test_api.py`                              |
| Evaluation endpoint exists                 | ✅     | `POST /v1/evaluations`                                                |
| Route layer is thin                        | ✅     | `app/routes/evaluations.py` only validates, delegates and maps errors |
| Service layer exists                       | ✅     | `app/services/evaluation_service.py` orchestrates and logs            |
| Core logic is reusable                     | ✅     | `evaluation/` never imports FastAPI; the CLI uses the same pipeline   |
| App does not contain metric logic directly | ✅     | All metrics live in `evaluation/`                                     |

Readiness notes:

```text
Local app readiness is met. A test confirms the API and the Python pipeline
produce identical results for the same request.
```

---

## 2. API readiness

Relevant files:

```text
app/main.py
app/routes/evaluations.py
app/schemas.py
app/services/evaluation_service.py
tests/test_api.py
tests/test_schemas.py
```

Checklist:

| Check                               | Status | Notes                                                                    |
| ----------------------------------- | ------ | ------------------------------------------------------------------------ |
| Request schema is explicit          | ✅     | `EvaluationRequest` in `evaluation/contracts.py`; unknown fields rejected |
| Response schema is explicit         | ⚠️     | `EvaluationResponse` exists, but its `result` field is an untyped `dict` |
| Required fields are validated       | ✅     | Pydantic returns HTTP 422 for missing or invalid fields                  |
| Blank required strings are rejected | ✅     | Tested for IDs, prompts, references and slices in `tests/test_schemas.py` |
| Empty example lists are rejected    | ⚠️     | Enforced by the schema (`min_length=1`); no dedicated test yet           |
| Duplicate example IDs are handled   | ✅     | Rejected by the request schema; tested in `tests/test_api.py`            |
| Missing slice labels are handled    | ✅     | `slice` is a required field; blank values tested                         |
| API tests cover success path        | ✅     | `test_api_and_python_produce_identical_computed_results`                 |
| API tests cover error paths         | ✅     | Blank identities, duplicate and unpaired IDs                             |

Go / no-go:

```text
Go only if request and response contracts are explicit and tested.
```

---

## 3. Configuration readiness

The service should avoid hard-coded production settings.

Checklist:

| Check                                     | Status | Notes                                                                    |
| ----------------------------------------- | ------ | ------------------------------------------------------------------------ |
| Config file exists                        | ✅     | `EvaluationConfig` in `evaluation/contracts.py`, validated with bounds   |
| Runtime settings are documented           | ✅     | Model names, dataset version and full config are saved with every run    |
| Random seed is explicit                   | ✅     | `config.seed` (default 42), recorded in results                          |
| Environment-specific values are separated | ❌     | No environment-based settings yet; see the future list below             |
| Secrets are not committed                 | ✅     | No secrets in the repo; `.env` files are gitignored                      |
| Defaults are safe                         | ✅     | Synthetic data always yields `HOLD`; the decision is never "ship"        |

Future production config should include:

```text
APP_ENV
LOG_LEVEL
RUN_STORAGE_PATH
MODEL_PROVIDER
JUDGE_MODEL_NAME
REQUEST_TIMEOUT_SECONDS
MAX_EXAMPLES_PER_REQUEST
```

Readiness notes:

```text
Evaluation settings are explicit and versioned per run. Service-level settings
(environment, storage path, provider, timeouts) are not configurable yet; request
limits are currently fixed in the schema.
```

---

## 4. Testing readiness

Relevant folder:

```text
tests/
```

Current test categories:

| Area                   | Test file                                                                              |
| ---------------------- | -------------------------------------------------------------------------------------- |
| API behavior           | `tests/test_api.py`                                                                    |
| Schema validation      | `tests/test_schemas.py`                                                                |
| Data quality           | `tests/test_data_quality.py`                                                           |
| Judge parsing          | `tests/test_judge_parser.py`                                                           |
| Rubric validation      | `tests/test_rubric_schema.py`, `tests/test_rubric.py`                                  |
| LLM judge scaffold     | `tests/test_llm_judge.py`                                                              |
| Judge calibration      | `tests/test_judge_calibration.py`                                                      |
| Text metrics           | `tests/test_text_metrics.py`                                                           |
| A/B testing            | `tests/test_ab_testing.py`                                                             |
| Model comparison       | `tests/test_model_comparison.py`                                                       |
| Metrics summary        | `tests/test_metrics_summary.py`                                                        |
| Report generation      | `tests/test_pipeline.py`, `tests/test_api.py` (via `evaluation/comparison_report.py`)  |
| Search/index utilities | `tests/test_search_index.py`                                                           |
| Retrieval evaluation   | `tests/test_retrieval_metrics.py`                                                      |
| Failure tag trie       | `tests/test_tag_trie.py`                                                               |
| Failure taxonomy       | `tests/test_failure_taxonomy.py`                                                       |
| Anomalous outputs      | `tests/test_anomaly_detection.py`                                                      |
| Significance           | `tests/test_significance.py`                                                           |
| Workflow demos         | `tests/test_workflow_demos.py`                                                         |
| Statistical utilities  | `tests/test_statistics.py`, `tests/test_validation_edges.py`                           |

Checklist:

| Check                                        | Status | Notes                                                                 |
| -------------------------------------------- | ------ | --------------------------------------------------------------------- |
| Unit tests pass                              | ✅     | `pytest` runs in GitHub Actions on every push                         |
| API tests pass                               | ✅     | Valid and invalid requests covered                                    |
| Error-path tests exist                       | ✅     | Bad inputs, non-finite numbers, malformed judge output                |
| Deterministic tests avoid external LLM calls | ✅     | No network calls; placeholder judge and fixtures only                 |
| Metrics tests include edge cases             | ✅     | Empty input, zero vector, mismatched lengths                          |
| Calibration tests cover disagreements        | ✅     | `find_disagreements` covers label and score mismatches                |
| Report-generation tests exist                | ✅     | Committed report regenerated and diffed in CI                         |
| Test command is documented                   | ✅     | README quick start                                                    |

Go / no-go:

```text
No deployment if the full test suite does not pass.
```

---

## 5. Data-quality readiness

Relevant files:

```text
evaluation/data_quality.py
evaluation/contracts.py
```

Checklist:

| Check                                        | Status | Notes                                                              |
| -------------------------------------------- | ------ | ------------------------------------------------------------------ |
| Duplicate example IDs detected               | ✅     | Blocking error                                                     |
| Blank prompts detected                       | ✅     | Blocking error                                                     |
| Blank candidate responses detected           | ✅     | Blocking error                                                     |
| Missing references handled                   | ✅     | Warning in the checker; required by the reference-based API schema |
| Missing slice labels handled                 | ✅     | Warning in the checker; required by the API schema                 |
| Metadata issues detected                     | ✅     | Malformed metadata is a blocking error                             |
| Blocking vs warning issues are distinguished | ✅     | Errors stop the run (HTTP 400); warnings are reported              |
| Data-quality output is reportable            | ✅     | Issue codes and messages appear in results and the Markdown report |

Readiness principle:

```text
Evaluation quality depends on input quality.
```

Go / no-go:

```text
No ship decision should rely on evaluation data that fails blocking data-quality checks.
```

---

## 6. Evaluation reliability

Relevant files:

```text
evaluation/text_metrics.py
evaluation/ab_testing.py
evaluation/model_comparison.py
evaluation/statistics.py
evaluation/metrics_summary.py
evaluation/judge_calibration.py
evaluation/significance.py
docs/lexical_vs_semantic_metrics_design.md
docs/practical_vs_statistical_significance_design.md
```

Checklist:

| Check                                  | Status | Notes                                                                       |
| -------------------------------------- | ------ | --------------------------------------------------------------------------- |
| Lexical metrics exist                  | ✅     | ROUGE-L F1, unigram precision, token recall, exact-match accuracy           |
| Semantic baseline exists               | ⚠️     | Manual synonym-count cosine only; no pretrained embeddings                  |
| Metrics have tests                     | ✅     | Normal and edge cases                                                       |
| Metric limitations are documented      | ✅     | `docs/lexical_vs_semantic_metrics_design.md`                                |
| Paired comparison exists               | ✅     | Paired bootstrap over per-example differences                               |
| Confidence intervals are available     | ✅     | Overall and per slice, with configurable confidence level                   |
| Practical significance is documented   | ✅     | `minimum_effect` threshold and `evaluation/significance.py`                 |
| Slice-level review is supported        | ✅     | Slice guardrail can force `HOLD` (see the demo report)                      |
| Judge calibration exists               | ⚠️     | Implemented, but validated only on authored fixtures, not human labels      |
| Significance reporting language exists | ✅     | Four fixed verdicts; cautious wording in the report                         |

Go / no-go:

```text
A model comparison should not be judged only by one aggregate metric.
```

---

## 7. LLM-as-a-Judge readiness

Relevant files:

```text
evaluation/llm_judge.py
evaluation/judge_parser.py
evaluation/rubric_schema.py
evaluation/judge_calibration.py
examples/judge_workflow.py
docs/judge_calibration_workflow.md
```

Checklist:

| Check                                     | Status | Notes                                                                     |
| ----------------------------------------- | ------ | ------------------------------------------------------------------------- |
| Judge prompt scaffold exists              | ✅     | Deterministic structured prompt requiring JSON output                     |
| Placeholder judge exists                  | ✅     | Keeps tests deterministic                                                 |
| Judge output parser exists                | ✅     | Strict: duplicate keys, unknown fields and out-of-range scores rejected   |
| Rubric schema exists                      | ✅     | Pydantic-validated; weights must sum to 1.0                               |
| Judge calibration exists                  | ✅     | Agreement, Cohen's kappa, MAE and correlation                             |
| Disagreement analysis exists              | ✅     | `find_disagreements` lists label and score mismatches                     |
| Judge calibration threshold is documented | ✅     | Default 0.80 label and score agreement; optional kappa minimum            |
| Raw judge outputs can be preserved        | ⚠️     | Raw and parsed outputs saved in the demo; no live judge pipeline yet      |
| Malformed judge output is handled         | ✅     | `JudgeParseError`; overall score recomputed from the rubric               |

Go / no-go:

```text
Do not use judge scores for release decisions unless judge calibration passes.
```

---

## 8. Persistence and artifact readiness

Relevant files:

```text
evaluation/artifacts.py
docs/persistence_state_handling_design.md
docs/error_handling_service_reliability_note.md
```

Checklist:

| Check                                        | Status | Notes                                                                  |
| -------------------------------------------- | ------ | ---------------------------------------------------------------------- |
| Run metadata is defined                      | ✅     | Run ID, dataset name/version, model names, config, seed, pipeline version |
| Run artifacts are defined                    | ✅     | Request, per-example results, report, demos, manifest                  |
| Run directory structure is documented        | ✅     | See below and `docs/persistence_state_handling_design.md`              |
| Idempotency rules are documented             | ✅     | An existing run ID is rejected; a per-run lock prevents collisions     |
| Failed-run behavior is documented            | ✅     | Incomplete runs are discarded; only completed runs are published       |
| Report artifact is produced                  | ✅     | `report.md`                                                            |
| Raw inputs can be connected to final outputs | ✅     | Request and dataset SHA-256 hashes; per-example rows                   |
| Run manifest exists                          | ✅     | `manifest.json` with file hashes, source fingerprint and status        |

Run directory written by the CLI:

```text
runs/
  portfolio-demo-v1/
    request.json
    results.json
    report.md
    workflow_demos.json
    manifest.json
```

Go / no-go:

```text
Do not treat an evaluation as production-ready unless inputs, outputs, and reports are traceable.
```

---

## 9. Observability readiness

Observability is mostly a future extension, but the readiness criteria should be clear.

Checklist:

| Check                                 | Status | Notes                                                                 |
| ------------------------------------- | ------ | --------------------------------------------------------------------- |
| Structured logging plan exists        | ⚠️     | JSON log events per run with run ID; no request ID                    |
| Request ID strategy exists            | ❌     | Not implemented                                                       |
| Error logs are structured             | ⚠️     | `evaluation_failed` event with error type; unexpected errors use default logging |
| Latency metrics are planned           | ⚠️     | `duration_ms` logged per run; no metrics backend                      |
| Evaluation success rate is planned    | ⚠️     | Completed and failed events logged; not aggregated                    |
| Judge parsing failures are tracked    | ❌     | No live judge yet                                                     |
| Data-quality issue counts are tracked | ⚠️     | `quality_issue_count` logged per run; no trend tracking               |
| Calibration failures are tracked      | ❌     | Calibration runs only in the demo                                     |
| Metric drift is planned               | ⚠️     | Designed in `docs/monitoring_and_lifecycle.md`; not implemented       |

Future operational metrics:

```text
request_count
request_latency_seconds
evaluation_run_duration_seconds
evaluation_success_rate
evaluation_failure_rate
judge_parse_failure_rate
data_quality_blocking_issue_count
calibration_failure_rate
report_generation_failure_rate
```

Go / no-go:

```text
A production service should expose enough logs and metrics to debug failures.
```

---

## 10. Security and secrets readiness

Checklist:

| Check                                         | Status | Notes                                                                 |
| --------------------------------------------- | ------ | --------------------------------------------------------------------- |
| No secrets committed                          | ✅     | None in Git history                                                   |
| `.env` files ignored                          | ✅     | `.env` and `.env.*` in `.gitignore`                                   |
| External model keys are environment variables | ➖     | No external provider is called yet                                    |
| Input data sensitivity is considered          | ⚠️     | Logs exclude raw prompts and responses; run artifacts store them      |
| Raw judge prompts are handled carefully       | ⚠️     | Only synthetic fixtures today; no redaction or access controls        |
| Error responses avoid leaking internals       | ✅     | Validation and data-quality errors return messages, not stack traces  |
| Access control plan exists                    | ⚠️     | Required in the production design docs; not implemented               |
| Data retention policy is considered           | ❌     | No formal retention policy                                            |

Recommended `.gitignore` entries (all present):

```text
.env
*.env
__pycache__/
.pytest_cache/
.DS_Store
```

Go / no-go:

```text
Do not connect real model providers or sensitive datasets until secrets and data-handling rules are clear.
```

---

## 11. Documentation readiness

Relevant docs:

```text
README.md
docs/architecture_one_pager.md
docs/lexical_vs_semantic_metrics_design.md
docs/practical_vs_statistical_significance_design.md
docs/judge_calibration_workflow.md
docs/retrieval_evaluation_design.md
docs/failure_analysis_design.md
docs/persistence_state_handling_design.md
docs/error_handling_service_reliability_note.md
docs/monitoring_and_lifecycle.md
```

README should include:

| Section              | Status | Notes                                                        |
| -------------------- | ------ | ------------------------------------------------------------ |
| Project overview     | ✅     | Opening paragraph and status line                            |
| Architecture summary | ✅     | `app -> evaluation` dependency direction                     |
| Repository structure | ⚠️     | Folders described in prose; no directory tree                |
| Local setup          | ✅     | Quick start                                                  |
| Run command          | ✅     | API and CLI commands                                         |
| Test command         | ✅     | `python -m pytest -q`                                        |
| API example          | ✅     | `curl` request to `/v1/evaluations`                          |
| Core features        | ✅     | Implemented capabilities table                               |
| Design notes         | ✅     | Links to all design docs                                     |
| Known limitations    | ✅     | Current limits section                                       |
| Future improvements  | ⚠️     | Gaps listed; production extensions are in the docs, not the README |

Go / no-go:

```text
A reviewer should be able to understand, run, and test the project from the README.
```

---

## 12. Known limitations

Current known limitations:

* no real external LLM judge integration yet
* placeholder judge is deterministic but not realistic
* run persistence is local files only; no database-backed run history
* asynchronous run workflow is not implemented
* observability is limited to structured run-level log events; no metrics backend or dashboards
* authentication and authorization are not implemented
* no deployment configuration such as Docker; CI runs tests and the offline demo only
* no formal data retention policy

These are acceptable for the current project stage if they are documented clearly.

---

## 13. Go / no-go checklist

| Area                  | Go condition                                                 | Local demo |
| --------------------- | ------------------------------------------------------------ | ---------- |
| Tests                 | Full `pytest` suite passes                                   | ✅         |
| API                   | Main evaluation endpoint works                               | ✅         |
| Schema                | Request/response contracts are explicit                      | ✅         |
| Data quality          | Blocking issues are detected                                 | ✅         |
| Metrics               | Lexical and semantic baseline metrics are tested             | ✅         |
| Statistical reporting | Confidence intervals and practical thresholds are documented | ✅         |
| Judge                 | Judge parser, rubric schema, and calibration exist           | ✅         |
| Reports               | Report template or generator exists                          | ✅         |
| Persistence           | State-handling design is documented                          | ✅         |
| Security              | No secrets committed                                         | ✅         |
| Documentation         | README explains how to run and test                          | ✅         |
| Limitations           | Known gaps are clearly stated                                | ✅         |

Decision:

```text
Local demo readiness: Go. All local conditions above are met.

Production readiness: No-go until environment-based configuration, request
tracing, a metrics backend, authentication, a database for run history,
async execution, and real deployment configuration are implemented.
```