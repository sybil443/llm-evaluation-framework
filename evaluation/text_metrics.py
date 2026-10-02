"""Lexical text metrics and exact-match label metrics.

Lightweight, dependency-light reference-based metrics used by the
evaluation pipeline (evaluation/pipeline.py) and the semantic baseline
(evaluation/semantic.py). Whitespace tokenization; not full BLEU/ROUGE.
"""
from collections import Counter
import math

from evaluation.statistics import finite_values

def tokenize(text: str) -> list[str]:
    """Lowercase whitespace tokenizer for lightweight text metrics."""
    return text.lower().split()

def unigram_bleu_precision(candidate: str, reference: str) -> float:
    """
    Lightweight BLEU-style unigram precision.

    This is not a full BLEU implementation. It captures the main intuition:
    how much of the candidate output overlaps with the reference text.
    """
    candidate_tokens = tokenize(candidate)
    reference_tokens = tokenize(reference)

    if not candidate_tokens:
        return 0.0

    reference_counts = Counter(reference_tokens)
    overlap = 0

    for token in candidate_tokens:
        if reference_counts[token] > 0:
            overlap += 1
            reference_counts[token] -= 1

    return overlap / len(candidate_tokens)

def rouge_l_f1(candidate: str, reference: str) -> float:
    """
    Lightweight ROUGE-L F1 score based on longest common subsequence.
    """
    candidate_tokens = tokenize(candidate)
    reference_tokens = tokenize(reference)

    if not candidate_tokens or not reference_tokens:
        return 0.0

    lcs_length = _longest_common_subsequence_length(candidate_tokens, reference_tokens)

    precision = lcs_length / len(candidate_tokens)
    recall = lcs_length / len(reference_tokens)

    if precision + recall == 0:
        return 0.0

    return 2 * precision * recall / (precision + recall)

def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    """
    Compute cosine similarity between two numeric vectors.

    In a full semantic-evaluation pipeline, these vectors would come from
    sentence embeddings. This function keeps the vector comparison logic
    deterministic and dependency-light.
    """
    if len(vector_a) != len(vector_b):
        raise ValueError("Vectors must have the same length.")

    vector_a = finite_values(vector_a, "vector_a")
    vector_b = finite_values(vector_b, "vector_b")
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)

def _longest_common_subsequence_length(tokens_a: list[str], tokens_b: list[str]) -> int:
    rows = len(tokens_a) + 1
    cols = len(tokens_b) + 1

    dp = [[0] * cols for _ in range(rows)]

    for i in range(1, rows):
        for j in range(1, cols):
            if tokens_a[i - 1] == tokens_b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[-1][-1]

def token_overlap_score(candidate: str, reference: str) -> float:
    """
    Calculate reference-token coverage by the candidate.

    This is a lightweight lexical recall-style metric:
    how much of the reference text is covered by the candidate output.
    """
    candidate_tokens = tokenize(candidate)
    reference_tokens = tokenize(reference)

    if not candidate_tokens or not reference_tokens:
        return 0.0

    candidate_counts = Counter(candidate_tokens)
    reference_counts = Counter(reference_tokens)

    overlap = sum(
        min(candidate_counts[token], reference_counts[token])
        for token in reference_counts
    )

    return overlap / len(reference_tokens)

def exact_label_match_score(predicted: str, reference: str) -> float:
    """
    Return 1.0 when the predicted label exactly matches the reference label
    after normalization, otherwise return 0.0.

    This is exact-match accuracy, not F1.
    """
    predicted_normalized = str(predicted).lower().strip()
    reference_normalized = str(reference).lower().strip()

    return 1.0 if predicted_normalized == reference_normalized else 0.0

def accuracy_score(predictions: list[str], references: list[str]) -> float:
    """
    Calculate exact-match accuracy across a list of predictions and references.
    """
    if len(predictions) != len(references):
        raise ValueError("Predictions and references must have the same length.")

    if not predictions:
        raise ValueError("At least one prediction is required.")

    correct = sum(
        exact_label_match_score(predicted, reference)
        for predicted, reference in zip(predictions, references)
    )

    return correct / len(predictions)