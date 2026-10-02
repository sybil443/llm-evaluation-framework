"""Render the shared pipeline's computed results; no hard-coded demo metrics."""

def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def render_report(result: dict) -> str:
    comparison = result["comparison"]
    confidence = comparison["confidence_level"] * 100
    lines = [
        "# Baseline / challenger evaluation", "",
        f"Run: `{result['run_id']}`",
        f"Dataset: {_cell(result['dataset']['name'])} / {_cell(result['dataset']['version'])}",
        f"Data kind: **{result['dataset']['kind']}**",
        f"Provenance: {_cell(result['dataset']['provenance'])}",
        f"Primary metric: `{result['primary_metric']}`",
        f"Decision: **{result['decision']['status']}**", "",
        "## Overall metrics", "",
        "| Metric | Baseline | Challenger | Difference |",
        "|---|---:|---:|---:|",
    ]
    for metric, a in result["metric_means"]["baseline"].items():
        b = result["metric_means"]["challenger"][metric]
        lines.append(f"| {metric} | {a:.4f} | {b:.4f} | {b-a:+.4f} |")
    lines.extend([
        "", "## Paired primary-metric comparison", "",
        f"- Pairs: {comparison['n_pairs']}",
        f"- Difference (challenger − baseline): {comparison['mean_difference']:+.4f}",
        f"- {confidence:g}% percentile bootstrap interval: "
        f"[{comparison['ci_lower']:+.4f}, {comparison['ci_upper']:+.4f}]",
        f"- Resamples: {comparison['n_resamples']}; seed: {comparison['seed']}",
        f"- Positive-resample fraction: {comparison['positive_resample_fraction']:.4f} "
        "(descriptive bootstrap statistic, not a posterior probability)",
        "", "## Slices", "",
        f"| Slice | Pairs | Difference | {confidence:g}% interval | Sample minimum met |",
        "|---|---:|---:|---|---|",
    ])
    for label, value in result["slices"].items():
        lines.append(f"| {_cell(label)} | {value['n_pairs']} | {value['mean_difference']:+.4f} | "
                     f"[{value['ci_lower']:+.4f}, {value['ci_upper']:+.4f}] | {value['sufficient_n']} |")
    lines.extend(["", "## Decision reasons", ""])
    lines.extend(f"- {reason}" for reason in result["decision"]["reasons"])
    lines.extend(["", "## Quality and flagged examples", "",
                  f"Quality issues: {len(result['quality_issues'])}",
                  f"Flagged examples: {result['failure_summary']['flagged_examples']}", ""])
    for issue in result["quality_issues"]:
        lines.append(f"- {issue['code']} ({issue.get('example_id') or 'dataset'}): {issue['message']}")
    for row in result["rows"]:
        if row["failure_tags"]:
            lines.append(f"- {row['example_id']}: {', '.join(row['failure_tags'])}")
    lines.extend(["", "Flags indicate heuristic review candidates, not verified factual failures.",
                  "", "## Retrieval demonstration", "",
                  "Keyword 'password': " + ", ".join(result['retrieval_demo']['keyword_ids']),
                  "Flagged-record metadata filter: " + ", ".join(result['retrieval_demo']['flagged_ids']),
                  "", "## Traceability", "",
                  f"Request SHA-256: `{result['request_sha256']}`",
                  f"Dataset SHA-256: `{result['dataset_sha256']}`",
                  f"Pipeline version: `{result['pipeline_version']}`", "",
                  "## Limitations", ""])
    lines.extend(f"- {item}" for item in result["limitations"])
    return "\n".join(lines) + "\n"

