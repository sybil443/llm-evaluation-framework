from collections import Counter
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QualityIssue:
    severity: str
    code: str
    message: str
    example_id: str | None = None


def _get_example_id(example: dict[str, Any]) -> str | None:
    example_id = example.get("example_id")
    if example_id is None:
        return None
    return str(example_id)


def _is_blank_text(value: Any) -> bool:
    return not isinstance(value, str) or not value.strip()


def _get_metadata(example: dict[str, Any]) -> Any:
    if "metadata" not in example:
        return {}
    return example["metadata"]


def _parse_slice_labels(
    metadata: Any,
    slice_key: str,
) -> tuple[list[str] | None, bool]:
    if not isinstance(metadata, dict):
        return None, True

    if slice_key not in metadata:
        return [], False

    value = metadata[slice_key]
    if isinstance(value, str):
        label = value.strip()
        return ([label] if label else []), False

    if isinstance(value, list):
        labels: list[str] = []
        for item in value:
            if not isinstance(item, str):
                return None, True
            label = item.strip()
            if label:
                labels.append(label)
        return labels, False

    return None, True


def check_blank_prompt(examples: list[dict[str, Any]]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []

    for example in examples:
        if _is_blank_text(example.get("prompt")):
            issues.append(
                QualityIssue(
                    severity="error",
                    code="BLANK_PROMPT",
                    message="Prompt must not be blank.",
                    example_id=_get_example_id(example),
                )
            )

    return issues


def check_blank_candidate_response(
    examples: list[dict[str, Any]],
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []

    for example in examples:
        if _is_blank_text(example.get("candidate_response")):
            issues.append(
                QualityIssue(
                    severity="error",
                    code="BLANK_CANDIDATE_RESPONSE",
                    message="Candidate response must not be blank.",
                    example_id=_get_example_id(example),
                )
            )

    return issues


def check_missing_example_id(
    examples: list[dict[str, Any]],
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []

    for example in examples:
        example_id = example.get("example_id")

        if not isinstance(example_id, str) or not example_id.strip():
            issues.append(
                QualityIssue(
                    severity="error",
                    code="MISSING_EXAMPLE_ID",
                    message="example_id must be a non-empty string.",
                )
            )

    return issues


def check_duplicate_ids(
    examples: list[dict[str, Any]],
) -> list[QualityIssue]:
    seen: set[str] = set()
    issues: list[QualityIssue] = []

    for example in examples:
        raw_example_id = example.get("example_id")

        if not isinstance(raw_example_id, str):
            continue

        example_id = raw_example_id.strip()

        if not example_id:
            continue

        if example_id in seen:
            issues.append(
                QualityIssue(
                    severity="error",
                    code="DUPLICATE_EXAMPLE_ID",
                    message=f"Duplicate example_id: {example_id}",
                    example_id=example_id,
                )
            )

        seen.add(example_id)

    return issues


def check_missing_reference_response(
    examples: list[dict[str, Any]],
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []

    for example in examples:
        reference_response = example.get("reference_response")
        if reference_response is None or _is_blank_text(reference_response):
            issues.append(
                QualityIssue(
                    severity="warning",
                    code="MISSING_REFERENCE_RESPONSE",
                    message="Reference response is missing or blank.",
                    example_id=_get_example_id(example),
                )
            )

    return issues


def check_malformed_metadata(
    examples: list[dict[str, Any]],
    *,
    slice_key: str = "slice",
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []

    for example in examples:
        metadata = _get_metadata(example)

        if not isinstance(metadata, dict):
            issues.append(
                QualityIssue(
                    severity="error",
                    code="MALFORMED_METADATA",
                    message="Metadata must be a mapping.",
                    example_id=_get_example_id(example),
                )
            )
            continue

        _, is_malformed = _parse_slice_labels(metadata, slice_key)
        if is_malformed:
            issues.append(
                QualityIssue(
                    severity="error",
                    code="MALFORMED_METADATA",
                    message=(
                        f"Metadata field '{slice_key}' must be a string or "
                        "list of strings."
                    ),
                    example_id=_get_example_id(example),
                )
            )

    return issues


def check_response_length(
    examples: list[dict[str, Any]],
    *,
    max_length: int,
) -> list[QualityIssue]:
    if max_length <= 0:
        raise ValueError("max_length must be positive.")

    issues: list[QualityIssue] = []

    for example in examples:
        candidate_response = example.get("candidate_response")
        if not isinstance(candidate_response, str):
            continue

        if len(candidate_response) > max_length:
            issues.append(
                QualityIssue(
                    severity="warning",
                    code="RESPONSE_TOO_LONG",
                    message=(
                        f"Candidate response length {len(candidate_response)} "
                        f"exceeds threshold {max_length}."
                    ),
                    example_id=_get_example_id(example),
                )
            )

    return issues


def check_missing_slice_labels(
    examples: list[dict[str, Any]],
    *,
    slice_key: str = "slice",
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []

    for example in examples:
        metadata = _get_metadata(example)
        labels, is_malformed = _parse_slice_labels(metadata, slice_key)

        if is_malformed or labels:
            continue

        issues.append(
            QualityIssue(
                severity="error",
                code="MISSING_SLICE_LABEL",
                message=f"Metadata is missing a non-empty '{slice_key}' label.",
                example_id=_get_example_id(example),
            )
        )

    return issues


def check_undersized_slices(
    examples: list[dict[str, Any]],
    *,
    min_slice_size: int,
    slice_key: str = "slice",
) -> list[QualityIssue]:
    if min_slice_size <= 0:
        raise ValueError("min_slice_size must be positive.")

    slice_counts: Counter[str] = Counter()

    for example in examples:
        metadata = _get_metadata(example)
        labels, is_malformed = _parse_slice_labels(metadata, slice_key)

        if is_malformed or not labels:
            continue

        for label in labels:
            slice_counts[label] += 1

    issues: list[QualityIssue] = []

    for slice_label, count in sorted(slice_counts.items()):
        if count < min_slice_size:
            issues.append(
                QualityIssue(
                    severity="warning",
                    code="UNDERSIZED_SLICE",
                    message=(
                        f"Slice '{slice_label}' has {count} examples, "
                        f"below minimum {min_slice_size}."
                    ),
                )
            )

    return issues


def run_data_quality_checks(
    examples: list[dict[str, Any]],
    *,
    max_response_length: int | None = None,
    min_slice_size: int | None = None,
    slice_key: str = "slice",
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    issues.extend(check_blank_prompt(examples))
    issues.extend(check_blank_candidate_response(examples))
    issues.extend(check_missing_example_id(examples))
    issues.extend(check_duplicate_ids(examples))
    issues.extend(check_missing_reference_response(examples))
    issues.extend(check_malformed_metadata(examples, slice_key=slice_key))
    issues.extend(check_missing_slice_labels(examples, slice_key=slice_key))

    if max_response_length is not None:
        issues.extend(
            check_response_length(examples, max_length=max_response_length)
        )

    if min_slice_size is not None:
        issues.extend(
            check_undersized_slices(
                examples,
                min_slice_size=min_slice_size,
                slice_key=slice_key,
            )
        )

    return issues
