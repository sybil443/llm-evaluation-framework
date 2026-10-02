"""Authored synthetic retrieval corpus, queries, and relevance judgments.

No real search engine or user click data produced these documents,
queries, or relevance grades. They are hand-authored to exercise ranking
metrics against three retrieval strategies already in this repo:

  - `search_by_keyword`, the pre-existing unranked substring lookup on
    `InMemorySearchIndex`. It requires the whole (normalized) query to
    appear verbatim in the text, so real multi-word queries usually
    match nothing. It is included below only as a descriptive "before"
    illustration, not as the baseline in the quantitative comparison,
    because comparing a ranker against a method that structurally
    cannot rank multi-word queries would be a strawman.
  - `term_overlap_rankings` (defined below), a naive but real ranking
    baseline: score by raw query-term overlap count, with no IDF
    weighting and no document-length normalization. This is the kind of
    approach a keyword-count search reaches for before adopting BM25,
    and it is the "baseline" used in `examples/retrieval_eval_demo.py`.
  - `search`, the BM25-ranked lookup added alongside this fixture, used
    as the "challenger" retriever.

Relevance grades are integers: 2 = directly answers the query, 1 =
related but only partially responsive, 0 (implicit, omitted) = not
relevant. Grades were authored by hand against the corpus text below,
not derived from any labeling process.
"""
from evaluation.search_index import InMemorySearchIndex, SearchItem, search_tokens

# item_id, text, metadata
DOCUMENTS = [
    ("doc-pwd-reset", "Reset your password from the account settings page after verifying your email.", {"topic": "account"}),
    ("doc-pwd-forgot", "If you forgot the password, request a reset link and set a new password.", {"topic": "account"}),
    ("doc-pwd-policy", "Password policy requires at least twelve characters and one number.", {"topic": "account"}),
    ("doc-account-delete", "Delete the account permanently from the account settings page.", {"topic": "account"}),
    ("doc-account-recover", "Recover a locked account using the backup passcode sent to your email.", {"topic": "account"}),
    ("doc-refund-eligible", "A delayed package qualifies for a refund if it arrives after the promised date.", {"topic": "billing"}),
    ("doc-refund-request", "Request a refund from the order history page within thirty days of purchase.", {"topic": "billing"}),
    ("doc-billing-invoice", "Download the billing invoice as a PDF from the account settings page.", {"topic": "billing"}),
    ("doc-shipment-cancel", "Cancel the shipment before it leaves the warehouse to avoid a delivery fee.", {"topic": "shipping"}),
    ("doc-shipment-track", "Track the shipment status using the tracking number emailed at checkout.", {"topic": "shipping"}),
    ("doc-shipment-delay", "A delayed shipment is automatically flagged and may qualify for a refund.", {"topic": "shipping"}),
    ("doc-backup-encrypt", "Encrypt the backup before saving it to remote storage to protect the data.", {"topic": "data"}),
    ("doc-backup-restore", "Restore the backup after verifying the encryption checksum matches.", {"topic": "data"}),
    ("doc-data-erase", "Erase account data permanently only after the backup restore is confirmed.", {"topic": "data"}),
]


def build_index() -> InMemorySearchIndex:
    index = InMemorySearchIndex()
    for item_id, text, metadata in DOCUMENTS:
        index.add_item(SearchItem(item_id=item_id, text=text, metadata=metadata))
    return index


# query_id -> query text
QUERIES = {
    "q-reset-password": "reset password account",
    "q-refund-delay": "refund delayed package",
    "q-cancel-shipment": "cancel shipment",
    "q-backup-data": "backup data encryption",
    "q-recover-account": "recover locked account",
}

# query_id -> {document_id: graded relevance}
JUDGMENTS = {
    "q-reset-password": {"doc-pwd-reset": 2, "doc-pwd-forgot": 2, "doc-pwd-policy": 1},
    "q-refund-delay": {"doc-refund-eligible": 2, "doc-shipment-delay": 2, "doc-refund-request": 1},
    "q-cancel-shipment": {"doc-shipment-cancel": 2, "doc-shipment-track": 1},
    "q-backup-data": {"doc-backup-encrypt": 2, "doc-backup-restore": 2, "doc-data-erase": 1},
    "q-recover-account": {"doc-account-recover": 2, "doc-pwd-forgot": 1},
}


def keyword_rankings(index: InMemorySearchIndex, *, k: int = 10) -> dict[str, list[str]]:
    """Descriptive only: pre-existing unranked substring keyword search.

    Not used as the comparison baseline (see module docstring) because it
    requires an exact substring match and returns nothing for realistic
    multi-word queries.
    """
    return {
        query_id: [item.item_id for item in index.search_by_keyword(query)][:k]
        for query_id, query in QUERIES.items()
    }


def term_overlap_rankings(index: InMemorySearchIndex, *, k: int = 10) -> dict[str, list[str]]:
    """Baseline retriever: rank by raw query-term overlap count.

    No IDF weighting and no document-length normalization, unlike BM25.
    Ties break by ascending item_id for determinism.
    """
    rankings = {}
    for query_id, query in QUERIES.items():
        query_tokens = search_tokens(query)
        scored = []
        for item in index.list_items():
            doc_tokens = search_tokens(item.text)
            overlap = sum(doc_tokens.count(token) for token in query_tokens)
            if overlap > 0:
                scored.append((item.item_id, overlap))
        scored.sort(key=lambda pair: (-pair[1], pair[0]))
        rankings[query_id] = [item_id for item_id, _ in scored[:k]]
    return rankings


def bm25_rankings(index: InMemorySearchIndex, *, k: int = 10) -> dict[str, list[str]]:
    """Challenger retriever: BM25-ranked search."""
    return {
        query_id: [hit.item_id for hit in index.search(query, k=k)]
        for query_id, query in QUERIES.items()
    }
