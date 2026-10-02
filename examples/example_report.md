# Baseline / challenger evaluation

Run: `portfolio-demo-v1`
Dataset: authored-evaluation-fixtures / 1.0
Data kind: **synthetic**
Provenance: Authored synthetic examples for software demonstration; no model or human evaluation study.
Primary metric: `rouge_l_f1`
Decision: **HOLD**

## Overall metrics

| Metric | Baseline | Challenger | Difference |
|---|---:|---:|---:|
| unigram_precision | 1.0000 | 0.8688 | -0.1312 |
| rouge_l_f1 | 0.6117 | 0.7360 | +0.1243 |
| token_recall | 0.5108 | 0.7138 | +0.2030 |
| concept_cosine | 0.8049 | 0.8703 | +0.0654 |

## Paired primary-metric comparison

- Pairs: 24
- Difference (challenger − baseline): +0.1243
- 95% percentile bootstrap interval: [-0.1041, +0.3478]
- Resamples: 2000; seed: 42
- Positive-resample fraction: 0.8550 (descriptive bootstrap statistic, not a posterior probability)

## Slices

| Slice | Pairs | Difference | 95% interval | Sample minimum met |
|---|---:|---:|---|---|
| support | 8 | +0.5417 | [+0.5208, +0.5556] | True |
| technical | 8 | -0.6108 | [-0.7258, -0.4532] | True |
| transport | 8 | +0.4421 | [+0.2413, +0.6018] | True |

## Decision reasons

- The primary-metric interval does not establish a positive difference.
- Slice regression exceeds guardrail: technical
- Synthetic fixtures cannot establish real model superiority.

## Quality and flagged examples

Quality issues: 0
Flagged examples: 9

- ex-009: lexical/low_reference_overlap, comparison/example_regression
- ex-017: lexical/low_reference_overlap, comparison/example_regression
- ex-018: lexical/low_reference_overlap, comparison/example_regression
- ex-019: comparison/example_regression
- ex-020: comparison/example_regression
- ex-021: lexical/low_reference_overlap, comparison/example_regression
- ex-022: comparison/example_regression
- ex-023: comparison/example_regression
- ex-024: lexical/low_reference_overlap, comparison/example_regression

Flags indicate heuristic review candidates, not verified factual failures.

## Retrieval demonstration

Keyword 'password': ex-001, ex-007, ex-019
Flagged-record metadata filter: ex-009, ex-017, ex-018, ex-019, ex-020, ex-021, ex-022, ex-023, ex-024

## Traceability

Request SHA-256: `56c2b860c49e500c944c768aac18876899ea6cb33d4e78abbaf13d077a567588`
Dataset SHA-256: `db43f5c7fa484b77e21cf45ff96a8f26075ba167a737ba2ee8dca90dec696f54`
Pipeline version: `1.0.0`

## Limitations

- Only ROUGE-L is the primary comparison metric; it is not factual correctness.
- Slice intervals are exploratory and unadjusted for multiple comparisons.
- Bootstrap assumes independent example pairs; clustered data need cluster resampling.
- Concept cosine ignores word order and negation and has a small manual vocabulary.
- No live judge is called; this result cannot certify judge reliability or safe deployment.
