# Bootstrap CI Utility

## What I built
A starter utility to compute a percentile bootstrap confidence interval for the sample mean.

## Why I built it
To practice evaluation tooling for model assessment, especially uncertainty-aware reporting.

## Inputs
- values
- n_bootstrap
- confidence_level
- seed

## Output
A dictionary containing:
- mean
- ci_lower
- ci_upper
- n_bootstrap
- confidence_level

## What I learned
- how bootstrap resampling works
- how to make the function reproducible with a seed
- how to design a small, reusable evaluation utility with tests

## Next steps
- support custom metrics
- add paired bootstrap for A/B comparisons
- integrate into evaluation reports