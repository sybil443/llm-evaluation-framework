# Metric definitions and limitations

| Metric | Definition | Limitation |
|---|---|---|
| `unigram_precision` | Clipped token overlap / candidate token count | Not full BLEU; no brevity penalty |
| `rouge_l_f1` | F1 of longest-common-subsequence precision/recall | Word overlap is not correctness |
| `token_recall` | Clipped token overlap / reference token count | Rewards reference coverage, not factuality |
| `concept_cosine` | Cosine of manually defined synonym-count vectors | Small vocabulary; ignores negation and word order |

Lexical tokenization lowercases and splits on whitespace; punctuation is retained.
The independent concept encoder uses lowercase alphabetic tokens. Its entire
vocabulary and version are persisted with each evaluation result.

## Semantic baseline evidence

`buy a fast car` and `purchase a quick automobile` map to identical concept vectors.
This demonstrates a semantic similarity baseline based on authored synonym groups,
not a learned representation. It requires no model download or network call.
Unknown texts get zero similarity and a `SEMANTIC_ZERO_COVERAGE` warning.

`the backup is safe` and `the backup is not safe` also get cosine 1.0. The demo and
tests intentionally preserve this blind spot. Never interpret this metric as
correctness, grounding, contradiction detection, or a production embedding benchmark.

## Failure analysis and behavioral slices

Support, transport, and technical scenarios are illustrative behavioral slices.
The pipeline reports their primary-metric means, paired differences, and intervals.
Heuristic tags flag low reference overlap and per-example regressions. A correct
paraphrase can be flagged; a factually wrong answer can receive a high score.
Flags support manual investigation; they are not verified model failures.

A production evaluation should add independently reviewed factuality labels,
challenge sets, task-specific safety rubrics, and an actual embedding model if needed.
Dataset/model provenance and metric versions must accompany any measured claim.