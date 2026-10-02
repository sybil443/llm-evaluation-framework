"""An interpretable semantic baseline, NOT pretrained sentence embeddings.

A dimension counts words from one manually defined synonym group. This toy
encoder resolves a few paraphrases but loses word order, negation and context.
Unknown words contribute nothing; zero coverage yields similarity 0 + a warning.
The full vocabulary/version is persisted with each run for reproducibility.
"""
import re

from evaluation.text_metrics import cosine_similarity

VERSION = "manual-concept-counts-v1"
CONCEPTS = (
    ("car", "automobile", "vehicle"),
    ("fast", "quick", "rapid"),
    ("buy", "purchase", "bought"),
    ("refund", "reimbursement", "refunded"),
    ("late", "delayed", "delay"),
    ("package", "parcel", "shipment"),
    ("help", "assist", "support"),
    ("cancel", "terminate", "stop"),
    ("account", "profile"),
    ("password", "passcode", "credential"),
    ("reset", "restore", "recover"),
    ("safe", "secure", "protected"),
    ("error", "failure", "fault"),
    ("save", "store", "persist"),
    ("data", "records", "information"),
    ("delete", "erase", "remove"),
    ("backup", "copy", "snapshot"),
    ("encrypt", "encryption", "encrypted"),
    ("contact", "call", "email"),
    ("before", "prior"),
)


def encode(text: str) -> list[float]:
    words = re.findall(r"[a-z]+", text.lower())
    return [float(sum(word in group for word in words)) for group in CONCEPTS]


def semantic_baseline(candidate: str, reference: str) -> tuple[float, bool]:
    a, b = encode(candidate), encode(reference)
    covered = any(a) and any(b)
    return cosine_similarity(a, b), bool(covered)