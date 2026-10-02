import pytest

from evaluation.data_quality import (
    check_blank_candidate_response,
    check_blank_prompt,
    check_duplicate_ids,
    check_malformed_metadata,
    check_missing_example_id,
    check_missing_reference_response,
    check_missing_slice_labels,
    check_response_length,
    check_undersized_slices,
    run_data_quality_checks,
)


def make_valid_example(**overrides) -> dict:
    example = {
        "example_id": "ex-1",
        "prompt": "Summarize the document.",
        "candidate_response": "A concise summary.",
        "reference_response": "Reference summary.",
        "metadata": {"slice": "short_prompt"},
    }
    example.update(overrides)
    return example


def test_check_blank_prompt_flags_blank_and_whitespace_values() -> None:
    examples = [
        make_valid_example(example_id="ex-1", prompt=""),
        make_valid_example(example_id="ex-2", prompt="   "),
    ]

    issues = check_blank_prompt(examples)

    assert len(issues) == 2
    assert all(issue.code == "BLANK_PROMPT" for issue in issues)
    assert all(issue.severity == "error" for issue in issues)


def test_check_blank_prompt_accepts_valid_prompt() -> None:
    assert check_blank_prompt([make_valid_example()]) == []


def test_check_blank_candidate_response_flags_blank_values() -> None:
    examples = [
        make_valid_example(example_id="ex-1", candidate_response=""),
        make_valid_example(example_id="ex-2", candidate_response="  "),
    ]

    issues = check_blank_candidate_response(examples)

    assert len(issues) == 2
    assert all(issue.code == "BLANK_CANDIDATE_RESPONSE" for issue in issues)


def test_check_blank_candidate_response_accepts_valid_response() -> None:
    assert check_blank_candidate_response([make_valid_example()]) == []


def test_check_duplicate_ids_flags_repeated_example_id() -> None:
    examples = [
        make_valid_example(example_id="ex-1"),
        make_valid_example(example_id="ex-1"),
    ]

    issues = check_duplicate_ids(examples)

    assert len(issues) == 1
    assert issues[0].code == "DUPLICATE_EXAMPLE_ID"
    assert issues[0].example_id == "ex-1"


def test_check_duplicate_ids_accepts_unique_ids() -> None:
    examples = [
        make_valid_example(example_id="ex-1"),
        make_valid_example(example_id="ex-2"),
    ]

    assert check_duplicate_ids(examples) == []


def test_check_missing_example_id_flags_missing_id() -> None:
    example = make_valid_example()
    del example["example_id"]

    issues = check_missing_example_id([example])

    assert len(issues) == 1
    assert issues[0].code == "MISSING_EXAMPLE_ID"
    assert issues[0].severity == "error"
    assert issues[0].example_id is None


def test_check_missing_example_id_flags_empty_id() -> None:
    issues = check_missing_example_id([make_valid_example(example_id="")])

    assert len(issues) == 1
    assert issues[0].code == "MISSING_EXAMPLE_ID"


def test_check_missing_example_id_flags_whitespace_only_id() -> None:
    issues = check_missing_example_id([make_valid_example(example_id="   ")])

    assert len(issues) == 1
    assert issues[0].code == "MISSING_EXAMPLE_ID"


def test_check_missing_example_id_flags_non_string_id() -> None:
    issues = check_missing_example_id([make_valid_example(example_id=123)])

    assert len(issues) == 1
    assert issues[0].code == "MISSING_EXAMPLE_ID"


def test_check_missing_example_id_accepts_valid_id() -> None:
    assert check_missing_example_id([make_valid_example(example_id="ex-1")]) == []


def test_check_missing_reference_response_flags_missing_and_blank_values() -> None:
    examples = [
        make_valid_example(example_id="ex-1", reference_response=None),
        make_valid_example(example_id="ex-2", reference_response="  "),
    ]

    issues = check_missing_reference_response(examples)

    assert len(issues) == 2
    assert all(issue.code == "MISSING_REFERENCE_RESPONSE" for issue in issues)
    assert all(issue.severity == "warning" for issue in issues)


def test_check_missing_reference_response_accepts_present_reference() -> None:
    assert check_missing_reference_response([make_valid_example()]) == []


def test_check_malformed_metadata_flags_non_mapping_metadata() -> None:
    issues = check_malformed_metadata(
        [make_valid_example(metadata="not-a-mapping")]
    )

    assert len(issues) == 1
    assert issues[0].code == "MALFORMED_METADATA"
    assert issues[0].message == "Metadata must be a mapping."


def test_check_malformed_metadata_flags_invalid_slice_type() -> None:
    issues = check_malformed_metadata(
        [make_valid_example(metadata={"slice": 123})]
    )

    assert len(issues) == 1
    assert issues[0].code == "MALFORMED_METADATA"
    assert "must be a string or list of strings" in issues[0].message


def test_check_malformed_metadata_accepts_valid_slice_labels() -> None:
    examples = [
        make_valid_example(metadata={"slice": "short_prompt"}),
        make_valid_example(example_id="ex-2", metadata={"slice": ["a", "b"]}),
    ]

    assert check_malformed_metadata(examples) == []


def test_check_response_length_flags_examples_over_threshold() -> None:
    issues = check_response_length(
        [make_valid_example(candidate_response="abcdef")],
        max_length=5,
    )

    assert len(issues) == 1
    assert issues[0].code == "RESPONSE_TOO_LONG"
    assert issues[0].severity == "warning"
    assert "length 6" in issues[0].message


def test_check_response_length_accepts_examples_at_or_below_threshold() -> None:
    assert check_response_length(
        [make_valid_example(candidate_response="abcde")],
        max_length=5,
    ) == []


def test_check_response_length_requires_positive_threshold() -> None:
    with pytest.raises(ValueError, match="max_length must be positive"):
        check_response_length([make_valid_example()], max_length=0)


def test_check_missing_slice_labels_flags_empty_or_missing_slice() -> None:
    examples = [
        make_valid_example(example_id="ex-1", metadata={}),
        make_valid_example(example_id="ex-2", metadata={"slice": ""}),
        make_valid_example(example_id="ex-3", metadata={"slice": ["", "  "]}),
    ]

    issues = check_missing_slice_labels(examples)

    assert len(issues) == 3
    assert all(issue.code == "MISSING_SLICE_LABEL" for issue in issues)


def test_check_missing_slice_labels_accepts_nonempty_slice_label() -> None:
    examples = [
        make_valid_example(metadata={"slice": "short_prompt"}),
        make_valid_example(example_id="ex-2", metadata={"slice": ["short", "long"]}),
    ]

    assert check_missing_slice_labels(examples) == []


def test_check_undersized_slices_flags_slices_below_minimum() -> None:
    examples = [
        make_valid_example(example_id="ex-1", metadata={"slice": "short"}),
        make_valid_example(example_id="ex-2", metadata={"slice": "long"}),
        make_valid_example(example_id="ex-3", metadata={"slice": "long"}),
    ]

    issues = check_undersized_slices(examples, min_slice_size=2)

    assert len(issues) == 1
    assert issues[0].code == "UNDERSIZED_SLICE"
    assert issues[0].example_id is None
    assert "Slice 'short' has 1 examples" in issues[0].message


def test_check_undersized_slices_accepts_slices_meeting_minimum() -> None:
    examples = [
        make_valid_example(example_id="ex-1", metadata={"slice": "short"}),
        make_valid_example(example_id="ex-2", metadata={"slice": "short"}),
    ]

    assert check_undersized_slices(examples, min_slice_size=2) == []


def test_check_undersized_slices_requires_positive_minimum() -> None:
    with pytest.raises(ValueError, match="min_slice_size must be positive"):
        check_undersized_slices([make_valid_example()], min_slice_size=0)


def test_run_data_quality_checks_returns_no_blocking_issues_for_valid_dataset() -> None:
    examples = [
        make_valid_example(example_id="ex-1", metadata={"slice": "short"}),
        make_valid_example(example_id="ex-2", metadata={"slice": "short"}),
    ]

    issues = run_data_quality_checks(examples)

    assert issues == []
    assert not any(issue.severity == "error" for issue in issues)


def test_run_data_quality_checks_detects_duplicate_id() -> None:
    examples = [
        make_valid_example(example_id="ex-1"),
        make_valid_example(example_id="ex-1"),
    ]

    issues = run_data_quality_checks(examples)

    duplicate_issues = [
        issue for issue in issues if issue.code == "DUPLICATE_EXAMPLE_ID"
    ]
    assert len(duplicate_issues) == 1
    assert duplicate_issues[0].severity == "error"


def test_run_data_quality_checks_detects_blank_candidate_response() -> None:
    issues = run_data_quality_checks(
        [make_valid_example(candidate_response="   ")]
    )

    blank_response_issues = [
        issue for issue in issues if issue.code == "BLANK_CANDIDATE_RESPONSE"
    ]
    assert len(blank_response_issues) == 1
    assert blank_response_issues[0].severity == "error"


def test_run_data_quality_checks_treats_missing_reference_as_warning() -> None:
    issues = run_data_quality_checks(
        [make_valid_example(reference_response=None)]
    )

    reference_issues = [
        issue for issue in issues if issue.code == "MISSING_REFERENCE_RESPONSE"
    ]
    assert len(reference_issues) == 1
    assert reference_issues[0].severity == "warning"


def test_run_data_quality_checks_returns_multiple_issues_together() -> None:
    examples = [
        make_valid_example(example_id="ex-1", prompt=""),
        make_valid_example(example_id="ex-1", candidate_response=""),
        make_valid_example(example_id="ex-2", reference_response=None),
        make_valid_example(example_id="ex-3", metadata={}),
    ]

    issues = run_data_quality_checks(examples)

    assert len(issues) >= 4
    codes = {issue.code for issue in issues}
    assert "BLANK_PROMPT" in codes
    assert "BLANK_CANDIDATE_RESPONSE" in codes
    assert "DUPLICATE_EXAMPLE_ID" in codes
    assert "MISSING_REFERENCE_RESPONSE" in codes
    assert "MISSING_SLICE_LABEL" in codes


def test_run_data_quality_checks_includes_optional_threshold_checks() -> None:
    examples = [
        make_valid_example(
            example_id="ex-1",
            candidate_response="abcdef",
            metadata={"slice": "short"},
        ),
        make_valid_example(
            example_id="ex-2",
            candidate_response="ghijkl",
            metadata={"slice": "short"},
        ),
    ]

    issues = run_data_quality_checks(
        examples,
        max_response_length=5,
        min_slice_size=3,
    )

    codes = {issue.code for issue in issues}
    assert "RESPONSE_TOO_LONG" in codes
    assert "UNDERSIZED_SLICE" in codes

@pytest.mark.parametrize(
    "example_id",
    [None, "", "   ", 123],
)
def test_check_missing_example_id_rejects_invalid_values(
    example_id,
) -> None:
    example = make_valid_example()
    example["example_id"] = example_id

    issues = check_missing_example_id([example])

    assert len(issues) == 1
    assert issues[0].code == "MISSING_EXAMPLE_ID"
    assert issues[0].severity == "error"