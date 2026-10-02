# LLM-as-a-Judge workflow and calibration

Status: executable workflow design with authored fixtures; no live judge integration.

`examples/judge_workflow.py` demonstrates:

1. Validate a versioned JSON rubric with unique criteria and normalized weights.
2. Build a judge prompt from structured example/reference/criterion inputs.
3. Supply explicitly authored fixture JSON to exercise parsing.
4. Validate the expected example ID, allowed fields, criterion set, finite score
   ranges, non-empty rationales, failure tags, and duplicate JSON keys.
5. Recompute the normalized weighted overall score from validated criterion scores.
6. Compare fixture scores/derived labels with fixture expectations, list disagreements,
   and apply explicit agreement thresholds.

The five expected judgments are authored demonstration values, not independent
human labels. Four are cases a two-criterion (correctness, clarity) judge should
get right; the fifth (`judge-5`) is a deliberate rubric-coverage gap — a fluent,
on-topic response that is unsafe advice, which correctness and clarity alone
score well. The fixture set passes its calibration gate overall (label and score
agreement both exactly at the default 0.80 threshold) while
`find_disagreements` still surfaces that one case, which is what a calibration
check is for: catching a specific miscalibration without requiring the whole
judge to be thrown out. `real_judge_validated` is always false. This result is
saved separately from the lexical model comparison and cannot establish
reliability of a real judge.

## The canonical rubric file
`evaluation/rubric_v0.yaml` is the one committed, versioned rubric. It is
loaded by `evaluation/rubric_schema.py`'s `load_rubric_schema_yaml()`, which
adapts the file's `criteria` mapping into `RubricSchema`'s list shape and
validates it with Pydantic: non-blank names and descriptions, positive
weights summing to 1.0, `min_score < max_score`, and unique criterion names.
`calculate_weighted_score()` in the same module normalizes each criterion
score into [0, 1] and applies the weights; `evaluation/judge_parser.py`
uses it to derive the overall score from a judge's per-criterion scores.

`run_judge_demo()`'s output includes a `canonical_rubric_v0` entry showing
the file loads through this path, though the fixture scoring above uses a
simpler two-criterion inline rubric (`RUBRIC` in `examples/judge_workflow.py`).

## Scoring contracts

Criterion scores use the rubric's bounds. Overall scores are normalized to [0,1].
The parser rejects structurally invalid totals; when a rubric is supplied, it
replaces the reported total with the rubric-derived weighted value. Callers must
supply the rubric and expected ID for full contextual validation. A bare parser
call can validate structure but cannot infer a criterion's permitted range.

## Calibration metrics

Beyond the exact-label-agreement rate and within-tolerance score-agreement
rate, `evaluation/judge_calibration.py`'s `summarize_calibration_results`
now also computes:

| Metric | What it adds beyond raw agreement rate |
|---|---|
| `cohens_kappa` | Corrects label agreement for the agreement expected by chance given each side's own label distribution; 0 means no better than chance, 1 means perfect. `None` when chance agreement is already 1.0 (kappa is undefined there, not any specific number). |
| `mean_absolute_score_error` | Average \|expected − judge\| score, in the rubric's own score units, independent of any pass/fail threshold. |
| `score_pearson_correlation` | Linear correlation between expected and judge scores. `None` for fewer than two examples or when either side has zero variance (undefined, not zero). |

Raw label-agreement rate can look good on an imbalanced label set (e.g.
mostly "pass" examples) even when the judge is barely better than chance;
kappa is the corrected check. `judge_passes_calibration` accepts an
optional `min_kappa` to enforce this as a gate condition; it is off by
default and raises if asked to check a summary with no computable kappa.

## Real calibration design

Use a held-out set with independent human judgments and a recorded labeling rubric.
Keep tuning examples separate. Examine disagreement by slice, task, prompt order,
and severity, including uncertainty on agreement rates. Tune on a development
split and evaluate on untouched examples; record all versions. Do not select
thresholds after seeing the held-out results.

Real provider integration would require model/version recording, timeouts,
bounded retries, rate limits, safe handling of raw prompts, and prompt-injection
resistance. Prompt construction here is a scaffold, not a security control.

