# Monitoring and model lifecycle design

Status: design document. Local run artifacts, version/hash traceability, and
run-scoped log events are implemented. Live monitoring, alerting, a model registry,
and deployment controls are not.

Two things have a lifecycle here: the models under evaluation, and the evaluator
itself (pipeline code, metric definitions, semantic encoder, rubric, judge prompt).
This repository implements traceability for the evaluator and its inputs. It does
not manage or observe deployed models.

## What is versioned today

| Item | Where recorded | Notes |
|---|---|---|
| Evaluator code | `pipeline_version` in `results.json`; source hashes in `manifest.json` | Any code change alters the source fingerprint |
| Metric definition | `primary_metric`; `semantic_encoder.version` and its full vocabulary | Changing either invalidates comparison with earlier runs |
| Dataset | `dataset.name`, `dataset.version`, `dataset_sha256` | Hash excludes run ID and config, so datasets are comparable across runs |
| Inputs and settings | `request_sha256` (covers config, seed, thresholds) | Identical hash plus pinned runtime reproduces scores and report bytes |
| Runtime | `python` and dependency versions in `manifest.json` | Timestamps are the only intended variation |
| Artifact integrity | Per-file SHA-256 in `manifest.json`; checked by `verify_run` | Detects accidental edits, not tampering |
| Judge prompt and rubric | `prompt_version`, rubric `version` in `workflow_demos.json` | Fixture workflow only; not part of `results.json` |

Not enforced: nothing checks that two runs are comparable (same `dataset_sha256`,
`primary_metric`, `semantic_encoder.version`, `pipeline_version`). `verify_run`
validates one run's integrity only. A cross-run comparability guard is proposed.

## Lifecycle stages

1. **Register versions.** Recorded per run (implemented). No central registry (proposed).
2. **Freeze evaluation set and thresholds.** Dataset hash and config are stored with
   each run (implemented). Setting thresholds before seeing results is a process
   requirement (see `practical_vs_statistical_significance_design.md`).
3. **Offline assessment.** Paired bootstrap, slice guardrails, and a decision of
   `INSUFFICIENT_EVIDENCE`, `HOLD`, or `REVIEW_CANDIDATE` (implemented). Human review
   and judge validation on independent labels are not implemented.
4. **Release decision.** The pipeline output is an input to human review, never an
   approval. Recording the reviewer, rationale, and exceptions is not implemented.
5. **Deploy, observe, roll back.** Out of scope for this repository.

## Monitoring signals

| Signal | Available from current outputs | Gap for live use | Response |
|---|---|---|---|
| Slice regressions | `slices[*]` difference and interval; guardrail reason in `decision.reasons` | Production traffic is not sliced or scored | Inspect affected slice and flagged examples; re-evaluate |
| Data quality | `quality_issues`; `SEMANTIC_ZERO_COVERAGE`; `failure_summary.tag_counts` | No trend tracking across runs | Investigate coverage gaps before trusting scores |
| Service health | `evaluation_started/completed/failed` events with `duration_ms`, `quality_issue_count`, `decision`, `error_type`; `/health` reports liveness only | No collection, dashboards, or readiness check | Check input size, error rate, latency |
| Judge reliability | Calibration disagreements, on authored fixtures only | No live judge and no independent labels | Recalibrate on held-out human labels; suspend affected judgments |
| Input distribution | None | Drift and coverage measures not implemented | Review dataset relevance before reuse |
| Version mismatch | Hashes and versions in each manifest | Cross-run guard not implemented | Refuse unsupported comparisons; repair lineage |

Guardrails such as `minimum_effect`, `max_slice_regression`, `min_pairs` and
`min_slice_size` are demo policies in `EvaluationConfig`, not alert thresholds.

## Controls for evaluation risks

- **Repeated benchmark tuning:** freeze the dataset by `dataset_sha256`; record
  thresholds before running; keep a separate held-out set.
- **Multiple testing:** slice intervals are exploratory and unadjusted (documented
  limitation). Holm correction is proposed.
- **Leakage and label contamination:** `data_kind` and `provenance` are recorded;
  no automated leakage check exists.
- **Judge drift:** pin the judge model and `prompt_version`; recalibrate after any change.

## Not implemented

Owners, alert thresholds, review cadence, retention, rollback criteria, dashboards,
and a live data feed. No monitoring signal is collected from a production
deployment by this repository.