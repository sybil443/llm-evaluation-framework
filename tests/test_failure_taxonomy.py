import json
from pathlib import Path

import pytest

from evaluation.failure_taxonomy import FailureTaxonomy, analyze_failure_tags, load_taxonomy


def _write(tmp_path: Path, payload) -> Path:
    path = tmp_path / "taxonomy.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_default_taxonomy_includes_the_pipelines_own_heuristic_tags() -> None:
    taxonomy = load_taxonomy()

    # evaluation/pipeline.py assigns these two tags; they must be registered.
    assert taxonomy.is_valid("lexical/low_reference_overlap")
    assert taxonomy.is_valid("comparison/example_regression")
    assert not taxonomy.is_valid("made_up/tag")


def test_category_is_the_part_before_the_first_slash() -> None:
    taxonomy = FailureTaxonomy(tags=frozenset({"quality/factuality", "safety"}))

    assert taxonomy.category("quality/factuality") == "quality"
    assert taxonomy.category("safety") == "safety"


def test_category_rejects_unknown_tag() -> None:
    taxonomy = FailureTaxonomy(tags=frozenset({"safety"}))

    with pytest.raises(ValueError, match="Unknown failure tag"):
        taxonomy.category("quality/factuality")


def test_validate_tags_lists_every_unknown_tag() -> None:
    taxonomy = FailureTaxonomy(tags=frozenset({"safety"}))

    taxonomy.validate_tags(["safety"])
    with pytest.raises(ValueError, match=r"\['a/x', 'b/y'\]"):
        taxonomy.validate_tags(["safety", "b/y", "a/x"])


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (["safety"], "failure_tags"),
        ({"tags": ["safety"]}, "failure_tags"),
        ({"failure_tags": []}, "at least one"),
        ({"failure_tags": ["safety", " "]}, "non-empty string"),
        ({"failure_tags": ["safety", 3]}, "non-empty string"),
        ({"failure_tags": ["safety", "safety"]}, "duplicate"),
    ],
)
def test_load_taxonomy_rejects_malformed_files(tmp_path: Path, payload, message) -> None:
    with pytest.raises(ValueError, match=message):
        load_taxonomy(_write(tmp_path, payload))


def test_load_taxonomy_reads_a_custom_file(tmp_path: Path) -> None:
    taxonomy = load_taxonomy(_write(tmp_path, {"failure_tags": ["format/json"]}))

    assert taxonomy.tags == frozenset({"format/json"})


def test_analyze_failure_tags_counts_by_tag_category_and_slice() -> None:
    taxonomy = FailureTaxonomy(tags=frozenset({"quality/factuality", "safety/privacy"}))
    rows = [
        {"slice": "support", "failure_tags": ["quality/factuality"]},
        {"slice": "support", "failure_tags": ["quality/factuality", "safety/privacy"]},
        {"slice": "technical", "failure_tags": []},
        {"failure_tags": ["new/unregistered"]},
    ]

    report = analyze_failure_tags(rows, taxonomy)

    assert report.total_rows == 4
    assert report.flagged_rows == 3
    assert report.tag_counts == {
        "quality/factuality": 2, "safety/privacy": 1, "new/unregistered": 1,
    }
    # Unknown tags are counted per tag and per slice, but have no category.
    assert report.category_counts == {"quality": 2, "safety": 1}
    assert report.counts_by_slice == {
        "support": {"quality/factuality": 2, "safety/privacy": 1},
        "unknown": {"new/unregistered": 1},
    }
    assert report.unknown_tags == ("new/unregistered",)


def test_analyze_failure_tags_rejects_empty_rows() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        analyze_failure_tags([], load_taxonomy())