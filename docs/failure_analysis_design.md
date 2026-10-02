# Failure taxonomy and anomalous-output detection

Status: implemented and tested against the authored demo evaluation
(examples/demo_data.py); not run against real model outputs or a
human-reviewed failure taxonomy.

## What this adds

| Component | File | Purpose |
|---|---|---|
| Failure taxonomy | `evaluation/failure_taxonomy.py` | Validates failure tags against a shared vocabulary; aggregates by tag, category, and slice |
| Taxonomy data | `examples/failure_taxonomy_example.json` | The vocabulary itself: quality/safety/format categories plus the pipeline's own heuristic tags |
| Anomaly detection | `evaluation/anomaly_detection.py` | Robust (median/MAD) statistical outlier flags over metric scores, metric deltas, and response length |
| Demo | `examples/failure_analysis_demo.py` | Runs both over `evaluate()`'s rows for the demo dataset |
| Wiring | `examples/run_llm_eval.py` | `run_failure_analysis_demo()` output saved as `failure_analysis` in `workflow_demos.json` |

Both modules are post-hoc analyses over `evaluation.pipeline.evaluate()`'s
returned `rows`, not changes to `evaluate()` itself: `evaluate()`'s return
shape is committed and diffed in CI (`examples/example_report.md`), and
this follows the same pattern already used for
`examples/retrieval_eval_demo.py` — a separate, importable, independently
tested layer rather than an addition to the pipeline's own output.

## Failure taxonomy

`evaluation/pipeline.py` already assigns two heuristic per-example tags
(`lexical/low_reference_overlap`, `comparison/example_regression`), and
`evaluation/llm_judge.py`'s judge output schema has a `failure_tags`
field. Neither was validated against anything before this: a typo in a
tag, or a new tag added to the pipeline and never registered anywhere,
would pass through silently. `evaluation/failure_taxonomy.py` loads the
vocabulary from `examples/failure_taxonomy_example.json` (which now
includes the pipeline's own tags alongside the original illustrative
quality/safety/format categories) and:

- validates a tag or list of tags against it (`is_valid`, `validate_tags`);
- maps a tag to its top-level category (`category`);
- aggregates a list of pipeline rows into tag counts, category counts,
  and a per-slice breakdown (`analyze_failure_tags`).

Tags on rows that are not in the taxonomy are reported in `unknown_tags`
rather than raising: evaluation should not crash because a new heuristic
tag was added to the pipeline and not yet registered here. That
"taxonomy drift" is exactly what the report is for.

## Anomalous-output detection

`evaluation/anomaly_detection.py` flags examples whose metric score,
metric delta (challenger minus baseline), or response length is a robust
statistical outlier within its own slice, using the modified z-score
(median and median absolute deviation, Iglewicz & Hoaglin's commonly
cited threshold of 3.5). It complements, but does not replace,
`evaluation/pipeline.py`'s two fixed-threshold heuristic tags: those use
configured cutoffs decided in advance, this uses the batch's own
distribution, so what counts as unusual depends on what else is in the
batch.

Outliers are computed **within each slice**, not across the whole mixed
dataset, by default (`group_by_slice=True`). On the demo fixture, scoring
globally instead flags nearly the entire `technical` slice (which is a
deliberately different, lower-overlap slice by design in
`examples/demo_data.py`) — that mostly re-states "this slice differs from
the others," which `evaluation/pipeline.py`'s own per-slice bootstrap
comparison already reports on its own terms. Grouping by slice instead
finds examples that are unusual **relative to their own peers**, which is
a different and more useful signal.

On the demo fixture, this correctly surfaces `ex-023` (`"the backup is
safe"` vs. challenger `"the backup is not safe"`) as a challenger-response
outlier within the `technical` slice: its ROUGE-L score is anomalously
*high* relative to its slice peers, because the challenger response
shares almost all its words with the reference, and only the negation is
different. This is the exact concept-cosine "negation blind spot" already
documented in `docs/lexical_vs_semantic_metrics_design.md`, now caught
independently by a general-purpose statistical outlier check rather than
hand-picked as a known case.

## Limitations

- Both modules ran against the 24-example authored demo fixture only.
  Nothing here has been validated against real model outputs, a larger
  corpus, or an independently authored failure taxonomy.
- An anomaly is a statistical outlier, not a verified failure: a
  genuinely excellent or unusually long response is also an outlier, and
  a consistently mediocre model produces none. Anomalies are candidates
  for human review, not conclusions.
- The modified z-score needs enough spread and enough examples per group
  to be meaningful. A slice with fewer than two examples is silently
  skipped, not force-scored, and a metric with no variation at all (every
  example gets the same score) yields no outliers.
- `evaluation/failure_taxonomy.py`'s taxonomy is a flat, two-level
  (category/subcategory) list, not a general tree, and it only counts and
  categorizes tags something else already assigned — it does not decide
  whether a response actually failed.
- Anomaly signals are computed independently per metric/side; nothing
  models a jointly unusual combination of signals that is not extreme on
  any one of them alone.
