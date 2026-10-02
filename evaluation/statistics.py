"""Single percentile-bootstrap implementation; no posterior probability claims."""
import math
from numbers import Real

import numpy as np


def finite_values(values, name="values") -> list[float]:
    if len(values) == 0:
        raise ValueError(f"{name} must not be empty.")
    if any(isinstance(x, bool) or not isinstance(x, Real) or not math.isfinite(x)
           for x in values):
        raise ValueError(f"{name} must contain finite numbers, excluding booleans.")
    return [float(x) for x in values]


def bootstrap_distribution(values, n_resamples=5000, seed=42):
    values = finite_values(values)
    if type(n_resamples) is not int or not 1 <= n_resamples <= 100_000:
        raise ValueError("n_resamples must be an integer between 1 and 100000.")
    if seed is not None and (type(seed) is not int or seed < 0):
        raise ValueError("seed must be a nonnegative integer or None.")
    rng = np.random.default_rng(seed)
    array = np.asarray(values, dtype=float)
    # One draw at a time keeps memory proportional to input size.
    return np.array([rng.choice(array, size=len(array), replace=True).mean()
                     for _ in range(n_resamples)])


def bootstrap_summary(values, n_resamples=5000, confidence_level=0.95, seed=42):
    values = finite_values(values)
    if (isinstance(confidence_level, bool)
            or not isinstance(confidence_level, Real)
            or not math.isfinite(confidence_level)
            or not 0 < confidence_level < 1):
        raise ValueError("confidence_level must be between 0 and 1.")
    means = bootstrap_distribution(values, n_resamples, seed)
    tail = (1 - confidence_level) / 2
    lower, upper = np.quantile(means, [tail, 1 - tail], method="linear")
    return {
        "mean": float(np.mean(values)), "ci_lower": float(lower),
        "ci_upper": float(upper), "confidence_level": float(confidence_level),
        "positive_resample_fraction": float(np.mean(means > 0)),
        "n": len(values), "n_resamples": n_resamples, "seed": seed,
    }


def paired_summary(scores_a, scores_b, n_resamples=5000,
                   confidence_level=0.95, seed=42):
    if len(scores_a) != len(scores_b):
        raise ValueError("Paired score arrays must have equal length.")
    if len(scores_a) == 0:
        raise ValueError("At least one score pair is required.")
    a = finite_values(scores_a, "scores_a")
    b = finite_values(scores_b, "scores_b")
    result = bootstrap_summary([y - x for x, y in zip(a, b)],
                               n_resamples, confidence_level, seed)
    result["mean_difference"] = result.pop("mean")
    result["n_pairs"] = result.pop("n")
    result.update(mean_a=float(np.mean(a)), mean_b=float(np.mean(b)))
    return result