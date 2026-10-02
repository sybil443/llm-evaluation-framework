import pytest

from evaluation.search_index import InMemorySearchIndex, SearchHit, SearchItem, search_tokens


def test_add_and_get_item() -> None:
    index = InMemorySearchIndex()
    item = SearchItem(
        item_id="rubric-correctness",
        text="Correctness measures whether the answer is factually right.",
        metadata={"type": "rubric"},
    )

    index.add_item(item)

    assert index.get_item("rubric-correctness") == item


def test_get_item_returns_none_for_missing_id() -> None:
    index = InMemorySearchIndex()

    assert index.get_item("missing") is None


def test_list_items_returns_added_items() -> None:
    index = InMemorySearchIndex()
    first_item = SearchItem(item_id="item-1", text="First item")
    second_item = SearchItem(item_id="item-2", text="Second item")

    index.add_item(first_item)
    index.add_item(second_item)

    assert index.list_items() == [first_item, second_item]


def test_search_by_keyword_matches_text_case_insensitively() -> None:
    index = InMemorySearchIndex()
    index.add_item(
        SearchItem(
            item_id="failure-factuality",
            text="Factuality failure means the answer contains incorrect facts.",
            metadata={"type": "failure_tag"},
        )
    )
    index.add_item(
        SearchItem(
            item_id="rubric-clarity",
            text="Clarity measures whether the answer is easy to understand.",
            metadata={"type": "rubric"},
        )
    )

    results = index.search_by_keyword("FACTUALITY")

    assert len(results) == 1
    assert results[0].item_id == "failure-factuality"


def test_search_by_keyword_returns_empty_list_for_blank_query() -> None:
    index = InMemorySearchIndex()
    index.add_item(SearchItem(item_id="item-1", text="Some text"))

    assert index.search_by_keyword("   ") == []


def test_search_by_metadata_returns_matching_items() -> None:
    index = InMemorySearchIndex()
    index.add_item(
        SearchItem(
            item_id="failure-factuality",
            text="Factuality failure",
            metadata={"type": "failure_tag"},
        )
    )
    index.add_item(
        SearchItem(
            item_id="rubric-correctness",
            text="Correctness criterion",
            metadata={"type": "rubric"},
        )
    )

    results = index.search_by_metadata("type", "rubric")

    assert len(results) == 1
    assert results[0].item_id == "rubric-correctness"


def test_search_by_metadata_rejects_blank_key() -> None:
    index = InMemorySearchIndex()

    with pytest.raises(ValueError, match="metadata key"):
        index.search_by_metadata("   ", "rubric")


def test_add_item_rejects_blank_item_id() -> None:
    index = InMemorySearchIndex()

    with pytest.raises(ValueError, match="item_id"):
        index.add_item(SearchItem(item_id="   ", text="Invalid item"))


def test_duplicate_item_id_replaces_existing_item() -> None:
    index = InMemorySearchIndex()

    index.add_item(SearchItem(item_id="item-1", text="Old text"))
    index.add_item(SearchItem(item_id="item-1", text="New text"))

    assert len(index) == 1
    assert index.get_item("item-1").text == "New text"

def test_null_metadata_filter_does_not_match_absent_key():
    index = InMemorySearchIndex()
    index.add_item(SearchItem("missing", "missing key", {}))
    index.add_item(SearchItem("explicit", "explicit null", {"category": None}))
    assert [item.item_id for item in index.search_by_metadata("category", None)] == ["explicit"]


def test_search_tokens_lowercases_and_splits_on_non_alphanumeric() -> None:
    assert search_tokens("Cats, Dogs & Birds!") == ["cats", "dogs", "birds"]


def build_ranking_index() -> InMemorySearchIndex:
    index = InMemorySearchIndex()
    index.add_item(SearchItem("cat", "the cat sat on the mat", {"topic": "animals"}))
    index.add_item(SearchItem("dog", "the dog sat on the log", {"topic": "animals"}))
    index.add_item(SearchItem("tech", "quantum computing is genuinely hard", {"topic": "tech"}))
    index.add_item(SearchItem("pets", "cats and dogs are common household pets", {"topic": "animals"}))
    return index


def test_search_returns_hits_ranked_by_score_descending() -> None:
    index = build_ranking_index()

    hits = index.search("cat")

    assert all(isinstance(hit, SearchHit) for hit in hits)
    assert hits[0].item_id == "cat"
    scores = [hit.score for hit in hits]
    assert scores == sorted(scores, reverse=True)


def test_search_hit_exposes_item_and_score() -> None:
    index = build_ranking_index()

    hits = index.search("cat")

    assert hits[0].item.item_id == "cat"
    assert hits[0].score > 0


def test_search_excludes_items_with_zero_overlap() -> None:
    index = build_ranking_index()

    hits = index.search("cat")

    assert "tech" not in [hit.item_id for hit in hits]


def test_search_returns_empty_list_for_blank_query() -> None:
    index = build_ranking_index()

    assert index.search("   ") == []


def test_search_returns_empty_list_when_no_terms_match() -> None:
    index = build_ranking_index()

    assert index.search("nonexistent_zzz_term") == []


def test_search_respects_k_limit() -> None:
    index = build_ranking_index()

    hits = index.search("the", k=1)

    assert len(hits) == 1


def test_search_rejects_non_positive_k() -> None:
    index = build_ranking_index()

    with pytest.raises(ValueError, match="k"):
        index.search("cat", k=0)


def test_search_applies_metadata_filters() -> None:
    index = build_ranking_index()

    hits = index.search("cat", filters={"topic": "tech"})

    assert hits == []


def test_search_filters_rejects_blank_key() -> None:
    index = build_ranking_index()

    with pytest.raises(ValueError, match="metadata key"):
        index.search("cat", filters={"   ": "animals"})


def test_search_breaks_ties_by_ascending_item_id() -> None:
    index = InMemorySearchIndex()
    index.add_item(SearchItem("b-item", "shared term shared term"))
    index.add_item(SearchItem("a-item", "shared term shared term"))

    hits = index.search("shared term")

    assert [hit.item_id for hit in hits] == ["a-item", "b-item"]


def test_search_is_stable_after_adding_more_items() -> None:
    index = InMemorySearchIndex()
    index.add_item(SearchItem("cat", "the cat sat on the mat"))
    first_hits = index.search("cat")

    index.add_item(SearchItem("extra", "an unrelated document about weather"))
    second_hits = index.search("cat")

    assert [hit.item_id for hit in first_hits] == [hit.item_id for hit in second_hits]


def test_constructor_rejects_invalid_k1_and_b() -> None:
    with pytest.raises(ValueError, match="k1"):
        InMemorySearchIndex(k1=-1)

    with pytest.raises(ValueError, match="b"):
        InMemorySearchIndex(b=1.5)

