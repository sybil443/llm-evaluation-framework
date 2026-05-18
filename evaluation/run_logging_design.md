# Run Logging Design

## Goal
Track evaluation runs in a consistent, reproducible way so that results can be audited, compared, and explained later.

## Why run logging matters
Evaluation results are only useful if the run conditions are clear. Logging helps answer:
- What inputs were used?
- What metric was computed?
- What seed and config produced the result?
- Which run generated a specific output?

## Core logged fields
Each run should record at least:
- `run_id`
- `timestamp`
- `metric_name`
- `n_bootstrap`
- `confidence_level`
- `seed`
- `input_size`
- `output_location`

## Optional useful fields
Later, the run log could also include:
- dataset name
- slice definition version
- code version or commit hash
- runtime
- notes or tags

## Run lifecycle
1. Start run
2. Assign or generate a run ID
3. Save run config
4. Execute evaluation utility
5. Save output summary
6. Record key metadata in run log

## Example log entry
```json
{
  "run_id": "bootstrap_run_001",
  "timestamp": "2026-05-16T18:00:00Z",
  "metric_name": "mean",
  "n_bootstrap": 1000,
  "confidence_level": 0.95,
  "seed": 42,
  "input_size": 5,
  "output_location": "evaluation/output/bootstrap_run_001.json"
}