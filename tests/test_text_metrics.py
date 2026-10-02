import pytest

from evaluation.text_metrics import (
    accuracy_score,
    cosine_similarity,
    exact_label_match_score,
    rouge_l_f1,
    token_overlap_score,
    unigram_bleu_precision,
)

def test_unigram_bleu_precision_counts_overlap() -> None:
    score = unigram_bleu_precision(
        candidate="the cat sat",
        reference="the cat slept",
    )

    assert score == pytest.approx(2 / 3)


def test_unigram_bleu_precision_returns_zero_for_empty_candidate() -> None:
    assert unigram_bleu_precision("", "reference text") == 0.0


def test_rouge_l_f1_uses_longest_common_subsequence() -> None:
    score = rouge_l_f1(
        candidate="the cat sat on mat",
        reference="the cat is on the mat",
    )

    assert score == pytest.approx(8 / 11)


def test_rouge_l_f1_returns_zero_for_empty_candidate() -> None:
    assert rouge_l_f1("", "reference text") == 0.0


def test_rouge_l_f1_returns_zero_for_empty_reference() -> None:
    assert rouge_l_f1("candidate text", "") == 0.0


def test_cosine_similarity_for_identical_vectors() -> None:
    assert cosine_similarity([1.0, 2.0], [1.0, 2.0]) == pytest.approx(1.0)


def test_cosine_similarity_for_orthogonal_vectors() -> None:
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_returns_zero_for_zero_vector() -> None:
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0


def test_cosine_similarity_rejects_different_lengths() -> None:
    with pytest.raises(ValueError, match="same length"):
        cosine_similarity([1.0], [1.0, 2.0])

def test_token_overlap_score_counts_reference_coverage() -> None:
    candidate = "the claim was delayed"
    reference = "the claim was delayed because documentation was missing"

    assert token_overlap_score(candidate, reference) == pytest.approx(4 / 8)

def test_exact_label_match_score_normalizes_strings() -> None:
    assert exact_label_match_score(" Positive ", "positive") == 1.0
    assert exact_label_match_score("negative", "positive") == 0.0


def test_accuracy_score_calculates_exact_match_accuracy() -> None:
    score = accuracy_score(
        predictions=["yes", "no", "yes", "yes"],
        references=["yes", "yes", "yes", "yes"],
    )

    assert score == pytest.approx(0.75)


def test_accuracy_score_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError, match="same length"):
        accuracy_score(["yes"], ["yes", "no"])