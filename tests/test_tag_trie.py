import pytest

from evaluation.tag_trie import TagTrie


def make_failure_tag_trie() -> TagTrie:
    trie = TagTrie()

    for tag in [
        "quality",
        "quality/factuality",
        "quality/relevance",
        "quality/completeness",
        "safety",
        "safety/privacy",
        "safety/toxicity",
        "format",
        "format/json",
        "format/citation",
    ]:
        trie.insert(tag)

    return trie


def test_insert_and_contains_existing_tag() -> None:
    trie = TagTrie()

    trie.insert("quality/factuality")

    assert trie.contains("quality/factuality")


def test_contains_returns_false_for_missing_tag() -> None:
    trie = make_failure_tag_trie()

    assert not trie.contains("quality/style")


def test_search_prefix_returns_matching_tags() -> None:
    trie = make_failure_tag_trie()

    result = trie.search_prefix("quality/")

    assert result == [
        "quality/completeness",
        "quality/factuality",
        "quality/relevance",
    ]


def test_search_prefix_returns_parent_tag_when_terminal() -> None:
    trie = make_failure_tag_trie()

    result = trie.search_prefix("quality")

    assert result == [
        "quality",
        "quality/completeness",
        "quality/factuality",
        "quality/relevance",
    ]


def test_search_prefix_returns_empty_list_for_unknown_prefix() -> None:
    trie = make_failure_tag_trie()

    assert trie.search_prefix("nonexistent/") == []


def test_insert_rejects_empty_tag() -> None:
    trie = TagTrie()

    with pytest.raises(ValueError, match="non-empty string"):
        trie.insert("   ")


def test_insert_rejects_non_string_tag() -> None:
    trie = TagTrie()

    with pytest.raises(TypeError, match="Tag must be a string"):
        trie.insert(123)  # type: ignore[arg-type]


def test_search_prefix_rejects_non_string_prefix() -> None:
    trie = make_failure_tag_trie()

    with pytest.raises(TypeError, match="Prefix must be a string"):
        trie.search_prefix(123)  # type: ignore[arg-type]


def test_duplicate_insert_is_idempotent() -> None:
    trie = TagTrie()

    trie.insert("format/json")
    trie.insert("format/json")

    assert trie.search_prefix("format/") == ["format/json"]


def test_slashes_are_normalized_for_tags() -> None:
    trie = TagTrie()

    trie.insert("/quality/factuality/")

    assert trie.contains("quality/factuality")
    assert trie.search_prefix("quality/") == ["quality/factuality"]