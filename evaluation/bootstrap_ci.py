import random
from statistics import mean
from typing import Any

def bootstrap_mean_ci(
    values: list[float],
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95,
    seed: int | None = None,
) -> dict[str, Any]:
    """
    Compute a percentile bootstrap confidence interval for the sample mean.
    Args:
        values: Input numeric values.
        n_bootstrap: Number of bootstrap samples to draw.
        confidence_level: Confidence level between 0 and 1.
        seed: Optional Random seed for reproducibility.

    Returns: 
        A dictionary containing the following keys:
        - "ci_lower": The lower bound of the confidence interval.
        - "ci_upper": The upper bound of the confidence interval.
        - "n_bootstrap": Number of bootstrap samples drawn.
        - "confidence_level": Confidence level used.
        - "original_mean": The original mean of the input values.
        - "original_n": Number of input values.

    Example:
        >>> bootstrap_mean_ci([1, 2, 3, 4, 5])
        {'mean': 3.0, 'ci_lower': 2.0, 'ci_upper': 4.0}
    """
    if not values:
        raise ValueError("Input values must not be empty")
    if n_bootstrap <= 0:
        raise ValueError("Number of bootstrap samples must be positive")
    if not (0< confidence_level <  1):
        raise ValueError("Confidence level must be between 0 and 1")

    rng = random.Random(seed)
    sample_size = len(values)
    original_mean = mean(values)

    bootstrap_means = []
    for _ in range(n_bootstrap):
        bootstrap_sample = [rng.choice(values) for _ in range(sample_size)]
        bootstrap_means.append(mean(bootstrap_sample))
        
    bootstrap_means.sort()
    alpha = 1 - confidence_level
    lower_pct = alpha / 2
    upper_pct = 1 - alpha / 2

    lower_idx = int(lower_pct * (n_bootstrap - 1))
    upper_idx = int(upper_pct * (n_bootstrap - 1))

    ci_lower = bootstrap_means[lower_idx]
    ci_upper = bootstrap_means[upper_idx]

    return {
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "n_bootstrap": n_bootstrap,
        "confidence_level": confidence_level,
        "original_mean": original_mean,
        "original_n": len(values),
    }