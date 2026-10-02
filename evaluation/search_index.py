"""In-memory search index: exact lookup, keyword/metadata filters, and BM25 ranking."""
from dataclasses import dataclass, field
import math
import re
from typing import Any

_TOKEN_PATTERN = re.compile(r"[^\W_]+")


def search_tokens(text: str) -> list[str]:
    """Lowercase alphanumeric tokenizer shared by indexing and querying."""
    return _TOKEN_PATTERN.findall(text.lower())


@dataclass(frozen=True)
class SearchItem:
    item_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchHit:
    """One ranked result: the item plus its BM25 score."""
    item: SearchItem
    score: float

    @property
    def item_id(self) -> str:
        return self.item.item_id


@dataclass(frozen=True)
class _CorpusStats:
    term_counts: dict[str, dict[str, int]]
    lengths: dict[str, int]
    average_length: float
    document_frequency: dict[str, int]


class InMemorySearchIndex:
    """
    Lightweight in-memory search index.

    This supports exact lookup, unranked keyword search, metadata
    filtering, and ranked BM25 search over the same items. It is
    intentionally dependency-free so it can be used in tests, scripts,
    notebooks, and future API service code.

    BM25 is a bag-of-words ranking function: it scores documents by
    term overlap with the query, weighted by how rare each term is
    across the corpus (IDF) and normalized for document length. It has
    no notion of synonyms, word order, or semantics, so it is a
    retrieval-ranking baseline, not a semantic search engine.
    """

    def __init__(self, *, k1: float = 1.5, b: float = 0.75) -> None:
        if k1 < 0:
            raise ValueError("k1 must be non-negative.")
        if not 0 <= b <= 1:
            raise ValueError("b must be between 0 and 1.")
        self._items: dict[str, SearchItem] = {}
        self._k1 = k1
        self._b = b
        self._stats: _CorpusStats | None = None

    def add_item(self, item: SearchItem) -> None:
        if not item.item_id.strip():
            raise ValueError("item_id must be non-empty.")

        self._items[item.item_id] = item
        self._stats = None

    def get_item(self, item_id: str) -> SearchItem | None:
        return self._items.get(item_id)

    def list_items(self) -> list[SearchItem]:
        return list(self._items.values())

    def search_by_keyword(self, query: str) -> list[SearchItem]:
        normalized_query = query.lower().strip()

        if not normalized_query:
            return []

        return [
            item
            for item in self._items.values()
            if normalized_query in item.text.lower()
        ]

    def search_by_metadata(self, key: str, value: Any) -> list[SearchItem]:
        if not key.strip():
            raise ValueError("metadata key must be non-empty.")

        return [
            item
            for item in self._items.values()
            if key in item.metadata and item.metadata[key] == value
        ]

    def _corpus_stats(self) -> _CorpusStats:
        if self._stats is not None:
            return self._stats
        term_counts: dict[str, dict[str, int]] = {}
        lengths: dict[str, int] = {}
        document_frequency: dict[str, int] = {}
        for item_id, item in self._items.items():
            tokens = search_tokens(item.text)
            lengths[item_id] = len(tokens)
            counts: dict[str, int] = {}
            for token in tokens:
                counts[token] = counts.get(token, 0) + 1
            term_counts[item_id] = counts
            for token in counts:
                document_frequency[token] = document_frequency.get(token, 0) + 1
        average_length = (sum(lengths.values()) / len(lengths)) if lengths else 0.0
        self._stats = _CorpusStats(term_counts, lengths, average_length, document_frequency)
        return self._stats

    def search(
        self, query: str, *, k: int = 10, filters: dict[str, Any] | None = None,
    ) -> list[SearchHit]:
        """
        Rank items against `query` using Okapi BM25 over `search_tokens`.

        `filters` restricts the candidate set to items whose metadata
        matches every key/value pair exactly (same semantics as
        `search_by_metadata`, applied before scoring). Ties in score are
        broken deterministically by ascending `item_id` so results are
        reproducible run to run. Items with a zero score are omitted;
        an empty or all-stopword-like query returns no hits.
        """
        if type(k) is not int or k < 1:
            raise ValueError("k must be a positive integer.")
        query_tokens = search_tokens(query)
        if not query_tokens:
            return []
        candidates = self._items.values()
        if filters:
            for key, value in filters.items():
                if not key.strip():
                    raise ValueError("metadata key must be non-empty.")
            candidates = [
                item for item in candidates
                if all(key in item.metadata and item.metadata[key] == value
                       for key, value in filters.items())
            ]
        stats = self._corpus_stats()
        n_docs = len(self._items)
        query_term_counts: dict[str, int] = {}
        for token in query_tokens:
            query_term_counts[token] = query_term_counts.get(token, 0) + 1
        hits = []
        for item in candidates:
            counts = stats.term_counts.get(item.item_id, {})
            length = stats.lengths.get(item.item_id, 0)
            score = 0.0
            for token in query_term_counts:
                freq = counts.get(token, 0)
                if freq == 0:
                    continue
                doc_freq = stats.document_frequency.get(token, 0)
                # Lucene-style non-negative IDF variant of Robertson-Sparck Jones.
                idf = math.log(1 + (n_docs - doc_freq + 0.5) / (doc_freq + 0.5))
                denom = freq + self._k1 * (
                    1 - self._b + self._b * (length / stats.average_length
                                             if stats.average_length else 0.0)
                )
                score += idf * (freq * (self._k1 + 1)) / denom
            if score > 0:
                hits.append(SearchHit(item=item, score=score))
        hits.sort(key=lambda hit: (-hit.score, hit.item_id))
        return hits[:k]

    def __len__(self) -> int:
        return len(self._items)
