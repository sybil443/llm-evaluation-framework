# Deployment Readiness Checklist

## Purpose

This checklist defines what needs to be true before the LLM evaluation framework is considered ready for a production-like deployment.

The goal is not to claim that the current project is fully production deployed. The goal is to document the readiness criteria, known gaps, and next engineering steps needed to move from a local FastAPI evaluation project toward a more reliable ML evaluation service.


---

## 1. Application readiness

| Check                                      | Status | Notes                                                   |
| ------------------------------------------ | ------ | ------------------------------------------------------- |
| FastAPI app starts locally                 |        | Confirm `uvicorn app.main:app --reload` works           |
| Health endpoint exists                     |        | Confirm `/health` or equivalent endpoint works          |
| Evaluation endpoint exists                 |        | Confirm `/v1/evaluations` or current route works        |
| Route layer is thin                        |        | Route should delegate to service layer                  |
| Service layer exists                       |        | Evaluation orchestration should live in `app/services/` |
| Core logic is reusable                     |        | Core evaluation code should live in `evaluation/`       |
| App does not contain metric logic directly |        | Metrics should stay outside route handlers              |

Readiness notes:

```text id="e6t3vx"
```

---

## 2. API readiness

Relevant files:

```text id="nm3rv8"
app/main.py
app/routes/evaluations.py
app/schemas.py
app/services/evaluation_service.py
tests/test_api.py
tests/test_schemas.py
```

Checklist:

| Check                               | Status | Notes                                                   |
| ----------------------------------- | ------ | ------------------------------------------------------- |
| Request schema is explicit          |        | `EvaluationRequest` or equivalent schema exists         |
| Response schema is explicit         |        | `EvaluationResponse` or equivalent schema exists        |
| Required fields are validated       |        | Missing fields should produce validation errors         |
| Blank required strings are rejected |        | Example IDs, prompts, and responses should not be blank |
| Empty example lists are rejected    |        | Prevent meaningless evaluation runs                     |
| Duplicate example IDs are handled   |        | Should be service/data-quality validation               |
| Missing slice labels are handled    |        | Should be service/data-quality validation               |
| API tests cover success path        |        | Valid request returns expected response                 |
| API tests cover error paths         |        | Invalid requests return expected errors                 |

Go / no-go:

```text id="q9k4fd"
Go only if request and response contracts are explicit and tested.
```

---

## 3. Configuration readiness

The service should avoid hard-coded production settings.

Checklist:

| Check                                     | Status | Notes                                                |
| ----------------------------------------- | ------ | ---------------------------------------------------- |
| Config file exists                        |        | `EvaluationConfig` in `evaluation/contracts.py`      |
| Runtime settings are documented           |        | Include model name, judge name, rubric version, seed |
| Random seed is explicit                   |        | Supports reproducibility                             |
| Environment-specific values are separated |        | Local vs production settings                         |
| Secrets are not committed                 |        | API keys should not appear in repo                   |
| Defaults are safe                         |        | Local defaults should not imply production readiness |

Future production config should include:

```text id="mps8br"
APP_ENV
LOG_LEVEL
RUN_STORAGE_PATH
MODEL_PROVIDER
JUDGE_MODEL_NAME
REQUEST_TIMEOUT_SECONDS
MAX_EXAMPLES_PER_REQUEST
```

Readiness notes:

```text id="mjbmoa"
```

---

## 4. Testing readiness

Relevant folder:

```text id="wtkvhc"
tests/
```

Current test categories should include:

| Area                   | Example test file                                                                      |
| ---------------------- | -------------------------------------------------------------------------------------- |
| API behavior           | `tests/test_api.py`                                                                    |
| Schema validation      | `tests/test_schemas.py`                                                                |
| Data quality           | `tests/test_data_quality.py`                                                           |
| Judge parsing          | `tests/test_judge_parser.py`                                                           |
| Rubric validation      | `tests/test_rubric_schema.py`,`tests/test_rubric.py`                                   |
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

| Check                                        | Status | Notes                                          |
| -------------------------------------------- | ------ | ---------------------------------------------- |
| Unit tests pass                              |        | Run `pytest`                                   |
| API tests pass                               |        | Include valid and invalid requests             |
| Error-path tests exist                       |        | Missing fields, bad data, invalid judge output |
| Deterministic tests avoid external LLM calls |        | Placeholder judge keeps tests stable           |
| Metrics tests include edge cases             |        | Empty input, zero vector, mismatched lengths   |
| Calibration tests cover disagreements        |        | Label mismatch and score mismatch              |
| Report-generation tests exist                |        | Prevent broken Markdown outputs                |
| Test command is documented                   |        | README should include `pytest` command         |

Go / no-go:

```text id="azy2to"
No deployment if the full test suite does not pass.
```

---

## 5. Data-quality readiness

Relevant files:

```text id="k1gf10"
evaluation/data_quality.py
evaluation/contracts.py
```

Checklist:

| Check                                        | Status | Notes                                           |
| -------------------------------------------- | ------ | ----------------------------------------------- |
| Duplicate example IDs detected               |        | Prevent incorrect joins and aggregation         |
| Blank prompts detected                       |        | Prevent meaningless evaluations                 |
| Blank candidate responses detected           |        | Prevent invalid scoring                         |
| Missing references handled                   |        | Should be warning or blocking depending on task |
| Missing slice labels handled                 |        | Needed for slice-level analysis                 |
| Metadata issues detected                     |        | Prevent broken reporting                        |
| Blocking vs warning issues are distinguished |        | Not all issues should stop a run                |
| Data-quality output is reportable            |        | Include issue codes and messages                |

Readiness principle:

```text id="ks1bdz"
Evaluation quality depends on input quality.
```

Go / no-go:

```text id="t3b1su"
No ship decision should rely on evaluation data that fails blocking data-quality checks.
```

---

## 6. Evaluation reliability

Relevant files:

```text id="sc5guv"
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

| Check                                  | Status | Notes                                                     |
| -------------------------------------- | ------ | --------------------------------------------------------- |
| Lexical metrics exist                  |        | BLEU-style precision, ROUGE-L, exact match, token overlap |
| Semantic baseline exists               |        | Cosine similarity                                         |
| Metrics have tests                     |        | Include normal and edge cases                             |
| Metric limitations are documented      |        | Lexical vs semantic tradeoffs                             |
| Paired comparison exists               |        | Compare model outputs on same examples                    |
| Confidence intervals are available     |        | Avoid overclaiming differences                            |
| Practical significance is documented   |        | Define meaningful effect-size thresholds                  |
| Slice-level review is supported        |        | Avoid hiding regressions in aggregates                    |
| Judge calibration exists               |        | Do not trust judge scores blindly                         |
| Significance reporting language exists |        | Standardize cautious conclusions                          |

Go / no-go:

```text id="y58r9n"
A model comparison should not be judged only by one aggregate metric.
```

---

## 7. LLM-as-a-Judge readiness

Relevant files:

```text id="xdr7kx"
evaluation/llm_judge.py
evaluation/judge_parser.py
evaluation/rubric_schema.py
evaluation/judge_calibration.py
examples/judge_workflow.py
docs/judge_calibration_workflow.md
```

Checklist:

| Check                                     | Status | Notes                                                 |
| ----------------------------------------- | ------ | ----------------------------------------------------- |
| Judge prompt scaffold exists              |        | Structured prompt construction                        |
| Placeholder judge exists                  |        | Keeps tests deterministic                             |
| Judge output parser exists                |        | Raw outputs must be parsed before use                 |
| Rubric schema exists                      |        | Criteria and weights are validated                    |
| Judge calibration exists                  |        | Compare judge labels/scores to expected labels/scores |
| Disagreement analysis exists              |        | Identify label and score mismatches                   |
| Judge calibration threshold is documented |        | Example: agreement rates above 0.80                   |
| Raw judge outputs can be preserved        |        | Needed for debugging                                  |
| Malformed judge output is handled         |        | Do not silently aggregate bad outputs                 |

Go / no-go:

```text id="fd0ic4"
Do not use judge scores for release decisions unless judge calibration passes.
```

---

## 8. Persistence and artifact readiness

Relevant files:

```text id="d7exvc"
evaluation/artifacts.py
docs/persistence_state_handling_design.md
docs/error_handling_service_reliability_note.md
```

Checklist:

| Check                                        | Status | Notes                                    |
| -------------------------------------------- | ------ | ---------------------------------------- |
| Run metadata is defined                      |        | `run_id`, model, judge, rubric, seed     |
| Run artifacts are defined                    |        | Inputs, outputs, metrics, reports        |
| Run directory structure is documented        |        | File-based first version                 |
| Idempotency rules are documented             |        | Avoid silent overwrite of completed runs |
| Failed-run behavior is documented            |        | Preserve partial artifacts               |
| Report artifact is produced                  |        | Markdown report or template              |
| Raw inputs can be connected to final outputs |        | Needed for auditability                  |
| Future run manifest is documented            |        | Track artifact paths and status          |

Suggested run directory:

```text id="p9lqzn"
runs/
  eval-run-001/
    run_config.json
    input_examples.jsonl
    data_quality_results.json
    judge_outputs.jsonl
    parsed_results.jsonl
    calibration_summary.json
    metrics_summary.json
    report.md
    run_manifest.json
```

Go / no-go:

```text id="ua99zd"
Do not treat an evaluation as production-ready unless inputs, outputs, and reports are traceable.
```

---

## 9. Observability readiness

Observability is mostly a future extension, but the readiness criteria should be clear.

Checklist:

| Check                                 | Status | Notes                                 |
| ------------------------------------- | ------ | ------------------------------------- |
| Structured logging plan exists        |        | Include run ID and request ID         |
| Request ID strategy exists            |        | Needed for tracing API calls          |
| Error logs are structured             |        | Avoid unsearchable stack traces only  |
| Latency metrics are planned           |        | Track request and evaluation runtime  |
| Evaluation success rate is planned    |        | Track completed vs failed runs        |
| Judge parsing failures are tracked    |        | Important for LLM judge reliability   |
| Data-quality issue counts are tracked |        | Useful for monitoring dataset quality |
| Calibration failures are tracked      |        | Avoid judge drift                     |
| Metric drift is planned               |        | Useful for long-term model monitoring |

Future operational metrics:

```text id="q7wqmh"
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

```text id="vgr99j"
A production service should expose enough logs and metrics to debug failures.
```

---

## 10. Security and secrets readiness

Checklist:

| Check                                         | Status | Notes                                          |
| --------------------------------------------- | ------ | ---------------------------------------------- |
| No secrets committed                          |        | API keys should not be in Git                  |
| `.env` files ignored                          |        | Add to `.gitignore`                            |
| External model keys are environment variables |        | Future real judge integration                  |
| Input data sensitivity is considered          |        | Evaluation examples may contain sensitive text |
| Raw judge prompts are handled carefully       |        | Prompts may include user or business data      |
| Error responses avoid leaking internals       |        | No stack traces in API responses               |
| Access control plan exists                    |        | Needed before multi-user deployment            |
| Data retention policy is considered           |        | Run artifacts may contain sensitive records    |

Recommended `.gitignore` entries:

```text id="s3f3l2"
.env
*.env
__pycache__/
.pytest_cache/
.DS_Store
```

Go / no-go:

```text id="g8og56"
Do not connect real model providers or sensitive datasets until secrets and data-handling rules are clear.
```

---

## 11. Documentation readiness

Relevant docs:

```text id="w3e2ga"
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

| Section              | Status | Notes                                        |
| -------------------- | ------ | -------------------------------------------- |
| Project overview     |        | What the project does                        |
| Architecture summary |        | Explain `app → evaluation`                   |
| Repository structure |        | Show major folders                           |
| Local setup          |        | Install dependencies                         |
| Run command          |        | FastAPI command                              |
| Test command         |        | `pytest`                                     |
| API example          |        | Example request                              |
| Core features        |        | Metrics, rubric, judge, calibration, reports |
| Design notes         |        | Link to docs                                 |
| Known limitations    |        | Be clear about non-production gaps           |
| Future improvements  |        | Roadmap                                      |

Go / no-go:

```text id="s0nj6g"
A reviewer should be able to understand, run, and test the project from the README.
```

---

## 12. Known limitations

Current known limitations:

* no real external LLM judge integration yet
* placeholder judge is deterministic but not realistic
* persistence design is documented but not fully implemented
* asynchronous run workflow is not implemented
* observability is limited to structured run-level log events; no metrics backend or dashboards
* authentication and authorization are not implemented
* run artifact storage is not yet productionized
* no database-backed run history
* no deployment configuration such as Docker; CI runs tests and the offline demo only
* no production monitoring dashboard
* no formal data retention policy

These are acceptable for the current project stage if they are documented clearly.

---

## 13. Go / no-go checklist

| Area                  | Go condition                                                 |
| --------------------- | ------------------------------------------------------------ |
| Tests                 | Full `pytest` suite passes                                   |
| API                   | Main evaluation endpoint works                               |
| Schema                | Request/response contracts are explicit                      |
| Data quality          | Blocking issues are detected                                 |
| Metrics               | Lexical and semantic baseline metrics are tested             |
| Statistical reporting | Confidence intervals and practical thresholds are documented |
| Judge                 | Judge parser, rubric schema, and calibration exist           |
| Reports               | Report template or generator exists                          |
| Persistence           | State-handling design is documented                          |
| Security              | No secrets committed                                         |
| Documentation         | README explains how to run and test                          |
| Limitations           | Known gaps are clearly stated                                |

Decision:

```text id="sz8fc3"
Local demo readiness: Go if tests pass and README is clear.

Production readiness: No-go until persistence, observability, security, async execution, and real deployment configuration are implemented.
```