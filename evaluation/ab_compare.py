from statistics import mean
from typing import Any

from evaluation.bootstrap_ci import bootstrap_mean_ci


def compare_mean_delta(
    values_a: list[float],
    values_b: list[float],
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95,
    seed: int | None = None,
) -> dict[str, Any]:
    mean_a = mean(values_a)
    mean_b = mean(values_b)
    delta = mean_b - mean_a

    ci_a = bootstrap_mean_ci(values_a, n_bootstrap, confidence_level, seed)
    ci_b = bootstrap_mean_ci(values_b, n_bootstrap, confidence_level, seed)

    return {
        "mean_a": mean_a,
        "mean_b": mean_b,
        "delta": delta,
        "ci_a": ci_a,
        "ci_b": ci_b,
    }