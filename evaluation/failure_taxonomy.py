"""
Structured failure taxonomy: validates and aggregates failure tags.

Failure tags elsewhere in this repo (evaluation/pipeline.py's two heuristic
per-example tags, a judge's reported failure_tags in evaluation/llm_judge.py)
are free-form "category/subcategory" strings with no shared vocabulary to
check them against. This module makes that vocabulary explicit and
loadable (examples/failure_taxonomy_example.json), validates tags against
it, and aggregates tagged rows into a report broken down by category and
by slice.

Limitations, stated up front:
  - The taxonomy is a flat, two-level (category/subcategory) list of
    strings, not a general tree; a tag with more than one "/" is treated
    as belonging to the category before the first "/".
  - Tags encountered on rows but absent from the taxonomy are reported in
    `unknown_tags`, not raised on. Evaluation should not crash because a
    new heuristic tag was added to the pipeline and not yet registered
    here; the report is how that drift becomes visible.
  - This module counts and categorizes tags that something else already
    assigned (evaluation/pipeline.py's heuristics, or a judge's output).
    It does not itself decide whether a response failed.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_TAXONOMY_PATH = Path(__file__).resolve().parents[1] / "examples" / "failure_taxonomy_example.json"


@dataclass(frozen=True)
class FailureTaxonomy:
    tags: frozenset[str]

    def is_valid(self, tag: str) -> bool:
        return tag in self.tags

    def category(self, tag: str) -> str:
        """Top-level category for a tag, e.g. 'quality/factuality' -> 'quality'."""
        if not self.is_valid(tag):
            raise ValueError(f"Unknown failure tag: {tag!r}")
        return tag.split("/", 1)[0]

    def validate_tags(self, tags) -> None:
        """Raise if any of `tags` is not part of this taxonomy."""
        unknown = sorted(set(tags) - self.tags)
        if unknown:
            raise ValueError(f"Unknown failure tags: {unknown}")


def load_taxonomy(path: str | Path | None = None) -> FailureTaxonomy:
    """Load a FailureTaxonomy from a JSON file shaped like {"failure_tags": [...]}."""
    taxonomy_path = Path(path) if path is not None else DEFAULT_TAXONOMY_PATH
    payload = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("failure_tags"), list):
        raise ValueError("Taxonomy file must contain a 'failure_tags' list.")
    tags = payload["failure_tags"]
    if not tags:
        raise ValueError("Taxonomy must define at least one failure tag.")
    if any(not isinstance(t, str) or not t.strip() for t in tags):
        raise ValueError("Every failure tag must be a non-empty string.")
    if len(set(tags)) != len(tags):
        raise ValueError("Taxonomy must not contain duplicate tags.")
    return FailureTaxonomy(tags=frozenset(tags))


@dataclass(frozen=True)
class FailureTaxonomyReport:
    total_rows: int
    flagged_rows: int
    tag_counts: dict[str, int]
    category_counts: dict[str, int]
    counts_by_slice: dict[str, dict[str, int]]
    unknown_tags: tuple[str, ...]


def analyze_failure_tags(rows: list[dict[str, Any]], taxonomy: FailureTaxonomy) -> FailureTaxonomyReport:
    """
    Aggregate `failure_tags` on evaluation rows (as produced by
    evaluation.pipeline.evaluate) into tag/category/slice breakdowns.

    Each row is expected to have a `failure_tags` list and, optionally, a
    `slice` label (rows missing `slice` are grouped under "unknown").
    Tags not present in `taxonomy` are counted in `tag_counts` and
    `counts_by_slice` like any other tag, but excluded from
    `category_counts` (there is no category to attribute them to) and
    listed in `unknown_tags` instead.
    """
    if not rows:
        raise ValueError("rows must not be empty.")
    tag_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    counts_by_slice: dict[str, dict[str, int]] = {}
    unknown: set[str] = set()
    flagged_rows = 0
    for row in rows:
        tags = row.get("failure_tags", [])
        if tags:
            flagged_rows += 1
        slice_label = row.get("slice", "unknown")
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            by_slice = counts_by_slice.setdefault(slice_label, {})
            by_slice[tag] = by_slice.get(tag, 0) + 1
            if taxonomy.is_valid(tag):
                category = taxonomy.category(tag)
                category_counts[category] = category_counts.get(category, 0) + 1
            else:
                unknown.add(tag)
    return FailureTaxonomyReport(
        total_rows=len(rows), flagged_rows=flagged_rows, tag_counts=tag_counts,
        category_counts=category_counts, counts_by_slice=counts_by_slice,
        unknown_tags=tuple(sorted(unknown)),
    )
