import pytest

from evaluation.judge_calibration import (
    CalibrationExample,
    CalibrationSummary,
    calculate_cohens_kappa,
    calculate_exact_label_agreement,
    calculate_mean_absolute_score_error,
    calculate_score_pearson_correlation,
    calculate_within_tolerance_score_agreement,
    find_disagreements,
    judge_passes_calibration,
    summarize_calibration_results,
)


def make_calibration_examples() -> list[CalibrationExample]:
    return [
        CalibrationExample(
            example_id="ex-001",
            expected_label="pass",
            judge_label="pass",
            expected_score=4.0,
            judge_score=4.0,
            metadata={"slice": "clear_pass"},
        ),
        CalibrationExample(
            example_id="ex-002",
            expected_label="fail",
            judge_label="fail",
            expected_score=2.0,
            judge_score=2.4,
            metadata={"slice": "clear_fail"},
        ),
        CalibrationExample(
            example_id="ex-003",
            expected_label="pass",
            judge_label="fail",
            expected_score=4.0,
            judge_score=3.8,
            metadata={"slice": "label_mismatch"},
        ),
        CalibrationExample(
            example_id="ex-004",
            expected_label="fail",
            judge_label="pass",
            expected_score=2.0,
            judge_score=4.0,
            metadata={"slice": "factuality_failure"},
        ),
    ]


def test_calibration_example_rejects_blank_example_id() -> None:
    with pytest.raises(ValueError, match="example_id"):
        CalibrationExample(
            example_id="   ",
            expected_label="pass",
            judge_label="pass",
            expected_score=4.0,
            judge_score=4.0,
        )


def test_calibration_example_rejects_blank_expected_label() -> None:
    with pytest.raises(ValueError, match="expected_label"):
        CalibrationExample(
            example_id="ex-001",
            expected_label="   ",
            judge_label="pass",
            expected_score=4.0,
            judge_score=4.0,
        )


def test_calibration_example_rejects_blank_judge_label() -> None:
    with pytest.raises(ValueError, match="judge_label"):
        CalibrationExample(
            example_id="ex-001",
            expected_label="pass",
            judge_label="   ",
            expected_score=4.0,
            judge_score=4.0,
        )


def test_calculate_exact_label_agreement() -> None:
    examples = make_calibration_examples()

    agreement_rate = calculate_exact_label_agreement(examples)

    assert agreement_rate == 0.5


def test_calculate_exact_label_agreement_rejects_empty_examples() -> None:
    with pytest.raises(ValueError, match="At least one calibration example"):
        calculate_exact_label_agreement([])


def test_calculate_within_tolerance_score_agreement() -> None:
    examples = make_calibration_examples()

    agreement_rate = calculate_within_tolerance_score_agreement(
        examples=examples,
        tolerance=0.5,
    )

    assert agreement_rate == 0.75


def test_calculate_within_tolerance_score_agreement_rejects_empty_examples() -> None:
    with pytest.raises(ValueError, match="At least one calibration example"):
        calculate_within_tolerance_score_agreement(
            examples=[],
            tolerance=0.5,
        )


def test_calculate_within_tolerance_score_agreement_rejects_negative_tolerance() -> None:
    examples = make_calibration_examples()

    with pytest.raises(ValueError, match="tolerance"):
        calculate_within_tolerance_score_agreement(
            examples=examples,
            tolerance=-0.1,
        )


def test_find_disagreements_returns_label_mismatch() -> None:
    examples = [
        CalibrationExample(
            example_id="ex-001",
            expected_label="pass",
            judge_label="fail",
            expected_score=4.0,
            judge_score=4.0,
            metadata={"slice": "label_only"},
        )
    ]

    disagreements = find_disagreements(examples=examples, tolerance=0.5)

    assert disagreements == [
        {
            "example_id": "ex-001",
            "expected_label": "pass",
            "judge_label": "fail",
            "expected_score": 4.0,
            "judge_score": 4.0,
            "score_difference": 0.0,
            "reason": "label_mismatch",
            "metadata": {"slice": "label_only"},
        }
    ]


def test_find_disagreements_returns_score_outside_tolerance() -> None:
    examples = [
        CalibrationExample(
            example_id="ex-001",
            expected_label="pass",
            judge_label="pass",
            expected_score=4.0,
            judge_score=2.5,
            metadata={"slice": "score_only"},
        )
    ]

    disagreements = find_disagreements(examples=examples, tolerance=0.5)

    assert disagreements == [
        {
            "example_id": "ex-001",
            "expected_label": "pass",
            "judge_label": "pass",
            "expected_score": 4.0,
            "judge_score": 2.5,
            "score_difference": 1.5,
            "reason": "score_outside_tolerance",
            "metadata": {"slice": "score_only"},
        }
    ]


def test_find_disagreements_returns_combined_mismatch_reason() -> None:
    examples = [
        CalibrationExample(
            example_id="ex-001",
            expected_label="fail",
            judge_label="pass",
            expected_score=2.0,
            judge_score=4.0,
            metadata={"slice": "combined"},
        )
    ]

    disagreements = find_disagreements(examples=examples, tolerance=0.5)

    assert disagreements == [
        {
            "example_id": "ex-001",
            "expected_label": "fail",
            "judge_label": "pass",
            "expected_score": 2.0,
            "judge_score": 4.0,
            "score_difference": 2.0,
            "reason": "label_mismatch_and_score_outside_tolerance",
            "metadata": {"slice": "combined"},
        }
    ]


def test_find_disagreements_excludes_matching_examples() -> None:
    examples = [
        CalibrationExample(
            example_id="ex-001",
            expected_label="pass",
            judge_label="pass",
            expected_score=4.0,
            judge_score=4.4,
            metadata={"slice": "matching"},
        )
    ]

    disagreements = find_disagreements(examples=examples, tolerance=0.5)

    assert disagreements == []


def test_find_disagreements_rejects_empty_examples() -> None:
    with pytest.raises(ValueError, match="At least one calibration example"):
        find_disagreements(examples=[], tolerance=0.5)


def test_find_disagreements_rejects_negative_tolerance() -> None:
    examples = make_calibration_examples()

    with pytest.raises(ValueError, match="tolerance"):
        find_disagreements(examples=examples, tolerance=-0.1)


def test_summarize_calibration_results() -> None:
    examples = make_calibration_examples()

    summary = summarize_calibration_results(
        examples=examples,
        tolerance=0.5,
    )

    assert isinstance(summary, CalibrationSummary)
    assert summary.total_examples == 4
    assert summary.exact_label_agreement_rate == 0.5
    assert summary.within_tolerance_score_agreement_rate == 0.75
    assert summary.tolerance == 0.5
    assert len(summary.disagreements) == 2
    assert summary.disagreements[0]["example_id"] == "ex-003"
    assert summary.disagreements[0]["reason"] == "label_mismatch"
    assert summary.disagreements[1]["example_id"] == "ex-004"
    assert summary.disagreements[1]["reason"] == (
        "label_mismatch_and_score_outside_tolerance"
    )


def test_summarize_calibration_results_uses_default_tolerance() -> None:
    examples = make_calibration_examples()

    summary = summarize_calibration_results(examples)

    assert summary.tolerance == 0.5


def test_summarize_calibration_results_rejects_empty_examples() -> None:
    with pytest.raises(ValueError, match="At least one calibration example"):
        summarize_calibration_results([])


def test_judge_passes_calibration_returns_true_when_thresholds_met() -> None:
    summary = CalibrationSummary(
        total_examples=10,
        exact_label_agreement_rate=0.9,
        within_tolerance_score_agreement_rate=0.85,
        tolerance=0.5,
        disagreements=[],
    )

    assert judge_passes_calibration(summary) is True


def test_judge_passes_calibration_returns_false_when_label_threshold_not_met() -> None:
    summary = CalibrationSummary(
        total_examples=10,
        exact_label_agreement_rate=0.7,
        within_tolerance_score_agreement_rate=0.9,
        tolerance=0.5,
        disagreements=[],
    )

    assert judge_passes_calibration(summary) is False


def test_judge_passes_calibration_returns_false_when_score_threshold_not_met() -> None:
    summary = CalibrationSummary(
        total_examples=10,
        exact_label_agreement_rate=0.9,
        within_tolerance_score_agreement_rate=0.7,
        tolerance=0.5,
        disagreements=[],
    )

    assert judge_passes_calibration(summary) is False


def test_judge_passes_calibration_supports_custom_thresholds() -> None:
    summary = CalibrationSummary(
        total_examples=10,
        exact_label_agreement_rate=0.75,
        within_tolerance_score_agreement_rate=0.75,
        tolerance=0.5,
        disagreements=[],
    )

    assert judge_passes_calibration(
        summary,
        min_label_agreement_rate=0.7,
        min_score_agreement_rate=0.7,
    ) is True


def test_judge_passes_calibration_rejects_invalid_label_threshold() -> None:
    summary = CalibrationSummary(
        total_examples=10,
        exact_label_agreement_rate=0.9,
        within_tolerance_score_agreement_rate=0.9,
        tolerance=0.5,
        disagreements=[],
    )

    with pytest.raises(ValueError, match="min_label_agreement_rate"):
        judge_passes_calibration(
            summary,
            min_label_agreement_rate=1.1,
        )


def test_judge_passes_calibration_rejects_invalid_score_threshold() -> None:
    summary = CalibrationSummary(
        total_examples=10,
        exact_label_agreement_rate=0.9,
        within_tolerance_score_agreement_rate=0.9,
        tolerance=0.5,
        disagreements=[],
    )

    with pytest.raises(ValueError, match="min_score_agreement_rate"):
        judge_passes_calibration(
            summary,
            min_score_agreement_rate=-0.1,
        )


# --- cohens_kappa / MAE / Pearson correlation ------------------------------


def test_calculate_cohens_kappa_is_zero_at_chance_level_agreement() -> None:
    examples = make_calibration_examples()

    assert calculate_cohens_kappa(examples) == pytest.approx(0.0)


def test_calculate_cohens_kappa_is_one_for_perfect_agreement() -> None:
    examples = [
        CalibrationExample("a", "pass", "pass", 4.0, 4.0),
        CalibrationExample("b", "fail", "fail", 2.0, 2.0),
        CalibrationExample("c", "pass", "pass", 4.5, 4.5),
    ]

    assert calculate_cohens_kappa(examples) == pytest.approx(1.0)


def test_calculate_cohens_kappa_is_none_when_chance_agreement_is_total() -> None:
    examples = [
        CalibrationExample("a", "pass", "pass", 4.0, 4.0),
        CalibrationExample("b", "pass", "pass", 4.5, 4.5),
    ]

    assert calculate_cohens_kappa(examples) is None


def test_calculate_cohens_kappa_rejects_empty_examples() -> None:
    with pytest.raises(ValueError, match="At least one calibration example"):
        calculate_cohens_kappa([])


def test_calculate_mean_absolute_score_error() -> None:
    examples = make_calibration_examples()

    assert calculate_mean_absolute_score_error(examples) == pytest.approx(0.65)


def test_calculate_mean_absolute_score_error_rejects_empty_examples() -> None:
    with pytest.raises(ValueError, match="At least one calibration example"):
        calculate_mean_absolute_score_error([])


def test_calculate_score_pearson_correlation_matches_hand_computed_value() -> None:
    examples = make_calibration_examples()

    assert calculate_score_pearson_correlation(examples) == pytest.approx(0.5232045649263551)


def test_calculate_score_pearson_correlation_is_none_for_a_single_example() -> None:
    examples = [CalibrationExample("a", "pass", "pass", 1.0, 1.0)]

    assert calculate_score_pearson_correlation(examples) is None


def test_calculate_score_pearson_correlation_is_none_when_judge_scores_are_constant() -> None:
    examples = [
        CalibrationExample("a", "pass", "pass", 1.0, 3.0),
        CalibrationExample("b", "fail", "fail", 2.0, 3.0),
    ]

    assert calculate_score_pearson_correlation(examples) is None


def test_summarize_calibration_results_includes_new_metrics() -> None:
    examples = make_calibration_examples()

    summary = summarize_calibration_results(examples)

    assert summary.cohens_kappa == pytest.approx(0.0)
    assert summary.mean_absolute_score_error == pytest.approx(0.65)
    assert summary.score_pearson_correlation == pytest.approx(0.5232045649263551)


def test_judge_passes_calibration_enforces_min_kappa_when_given() -> None:
    summary = CalibrationSummary(
        total_examples=10, exact_label_agreement_rate=0.9,
        within_tolerance_score_agreement_rate=0.9, tolerance=0.5,
        disagreements=[], cohens_kappa=0.2,
    )

    assert judge_passes_calibration(summary, min_kappa=0.5) is False
    assert judge_passes_calibration(summary, min_kappa=0.1) is True


def test_judge_passes_calibration_raises_when_min_kappa_given_but_unavailable() -> None:
    summary = CalibrationSummary(
        total_examples=10, exact_label_agreement_rate=0.9,
        within_tolerance_score_agreement_rate=0.9, tolerance=0.5,
        disagreements=[], cohens_kappa=None,
    )

    with pytest.raises(ValueError, match="cohens_kappa"):
        judge_passes_calibration(summary, min_kappa=0.5)


def test_judge_passes_calibration_rejects_invalid_min_kappa() -> None:
    summary = CalibrationSummary(
        total_examples=10, exact_label_agreement_rate=0.9,
        within_tolerance_score_agreement_rate=0.9, tolerance=0.5,
        disagreements=[], cohens_kappa=0.5,
    )

    with pytest.raises(ValueError, match="min_kappa"):
        judge_passes_calibration(summary, min_kappa=1.5)