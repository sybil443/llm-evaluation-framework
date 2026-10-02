"""Shared deterministic evaluation pipeline. No FastAPI or external model calls."""
from collections import Counter
from dataclasses import asdict
import hashlib
import json

from evaluation.contracts import EvaluationRequest
from evaluation.data_quality import run_data_quality_checks
from evaluation.text_metrics import rouge_l_f1, token_overlap_score, unigram_bleu_precision
from evaluation.metrics_summary import MetricRecord, summarize_metric_records
from evaluation.search_index import InMemorySearchIndex, SearchItem
from evaluation.semantic import CONCEPTS, VERSION, semantic_baseline
from evaluation.statistics import paired_summary

PIPELINE_VERSION = "1.0.0"
PRIMARY_METRIC = "rouge_l_f1"


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                      allow_nan=False) + "\n"


def digest(value) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def canonical_request(request: EvaluationRequest) -> dict:
    payload = request.model_dump()
    for key in ("examples", "baseline", "challenger"):
        payload[key] = sorted(payload[key], key=lambda item: item["example_id"])
    return payload


def text_metrics(response, reference):
    semantic, covered = semantic_baseline(response, reference)
    return {
        "unigram_precision": unigram_bleu_precision(response, reference),
        "rouge_l_f1": rouge_l_f1(response, reference),
        "token_recall": token_overlap_score(response, reference),
        "concept_cosine": semantic,
    }, covered


def build_result_index(rows) -> InMemorySearchIndex:
    index = InMemorySearchIndex()
    for row in rows:
        index.add_item(SearchItem(
            item_id=row["example_id"],
            text=" ".join([row["prompt"], row["reference_response"],
                           row["baseline_response"], row["challenger_response"]]),
            metadata={"slice": row["slice"], "has_flags": bool(row["failure_tags"]),
                      "failure_tags": row["failure_tags"]},
        ))
    return index


def _comparison(rows, config):
    return paired_summary(
        [r["baseline_metrics"][PRIMARY_METRIC] for r in rows],
        [r["challenger_metrics"][PRIMARY_METRIC] for r in rows],
        config.n_bootstrap, config.confidence_level, config.seed,
    )


def evaluate(request: EvaluationRequest) -> dict:
    payload = canonical_request(request)
    config = request.config
    baseline = {x.example_id: x.response for x in request.baseline}
    challenger = {x.example_id: x.response for x in request.challenger}
    examples = sorted(request.examples, key=lambda x: x.example_id)
    quality_inputs = [dict(
        example_id=x.example_id, prompt=x.prompt,
        reference_response=x.reference_response, candidate_response=challenger[x.example_id],
        metadata={"slice": x.slice},
    ) for x in examples]
    quality = [asdict(issue) for issue in run_data_quality_checks(
        quality_inputs, min_slice_size=config.min_slice_size)]
    if any(issue["severity"] == "error" for issue in quality):
        raise ValueError("Blocking data-quality errors: " + canonical_json(quality))
    rows = []
    for example in examples:
        a, a_covered = text_metrics(baseline[example.example_id], example.reference_response)
        b, b_covered = text_metrics(challenger[example.example_id], example.reference_response)
        tags = []
        if b[PRIMARY_METRIC] < config.low_overlap_threshold:
            tags.append("lexical/low_reference_overlap")
        if b[PRIMARY_METRIC] - a[PRIMARY_METRIC] < -config.max_slice_regression:
            tags.append("comparison/example_regression")
        if not (a_covered and b_covered):
            quality.append(dict(severity="warning", code="SEMANTIC_ZERO_COVERAGE",
                                message="Concept encoder has no coverage for at least one text.",
                                example_id=example.example_id))
        rows.append(dict(
            example_id=example.example_id, prompt=example.prompt, slice=example.slice,
            reference_response=example.reference_response,
            baseline_response=baseline[example.example_id],
            challenger_response=challenger[example.example_id],
            baseline_metrics=a, challenger_metrics=b, failure_tags=tags,
        ))
    overall = _comparison(rows, config)
    slices = {}
    for label in sorted({x.slice for x in examples}):
        selected = [row for row in rows if row["slice"] == label]
        comparison = _comparison(selected, config)
        comparison["sufficient_n"] = len(selected) >= config.min_slice_size
        slices[label] = comparison
    means = {side: summarize_metric_records([
        MetricRecord(row["example_id"], row[f"{side}_metrics"], {"slice": row["slice"]})
        for row in rows
    ], slice_key="slice").metric_means for side in ("baseline", "challenger")}
    reasons = []
    insufficient = len(rows) < config.min_pairs or any(
        not summary["sufficient_n"] for summary in slices.values())
    if insufficient:
        reasons.append("Overall or slice sample size is below the configured review minimum.")
    if overall["ci_lower"] <= 0:
        reasons.append("The primary-metric interval does not establish a positive difference.")
    if overall["mean_difference"] < config.minimum_effect:
        reasons.append("Observed primary-metric lift is below the practical threshold.")
    regressions = [label for label, result in slices.items()
                   if result["mean_difference"] < -config.max_slice_regression]
    if regressions:
        reasons.append("Slice regression exceeds guardrail: " + ", ".join(regressions))
    if request.data_kind == "synthetic":
        reasons.append("Synthetic fixtures cannot establish real model superiority.")
    decision = ("INSUFFICIENT_EVIDENCE" if insufficient else
                "HOLD" if reasons else "REVIEW_CANDIDATE")
    if not reasons:
        reasons.append("Offline lexical gates passed; human quality, safety, and operational review required.")
    index = build_result_index(rows)
    return dict(
        schema_version="1.0", pipeline_version=PIPELINE_VERSION,
        run_id=request.run_id, request_sha256=digest(payload),
        dataset_sha256=digest({k: v for k, v in payload.items()
                               if k not in {"run_id", "config"}}),
        dataset=dict(name=request.dataset_name, version=request.dataset_version,
                     kind=request.data_kind, provenance=request.provenance),
        models=dict(baseline=request.baseline_name, challenger=request.challenger_name),
        config=config.model_dump(), primary_metric=PRIMARY_METRIC,
        semantic_encoder=dict(version=VERSION, concepts=CONCEPTS,
                              kind="manual synonym-count vectors; not pretrained embeddings"),
        quality_issues=quality, metric_means=means, comparison=overall,
        slices=slices, rows=rows,
        failure_summary=dict(flagged_examples=sum(bool(r["failure_tags"]) for r in rows),
                             tag_counts=dict(Counter(t for r in rows for t in r["failure_tags"]))),
        retrieval_demo=dict(
            query="password",
            keyword_ids=[x.item_id for x in index.search_by_keyword("password")],
            flagged_ids=[x.item_id for x in index.search_by_metadata("has_flags", True)],
            slice_ids={label: [x.item_id for x in index.search_by_metadata("slice", label)]
                       for label in slices}),
        decision=dict(status=decision, reasons=reasons),
        limitations=[
            "Only ROUGE-L is the primary comparison metric; it is not factual correctness.",
            "Slice intervals are exploratory and unadjusted for multiple comparisons.",
            "Bootstrap assumes independent example pairs; clustered data need cluster resampling.",
            "Concept cosine ignores word order and negation and has a small manual vocabulary.",
            "No live judge is called; this result cannot certify judge reliability or safe deployment.",
        ],
    )