# Reproducibility Note

## Goal
Make bootstrap CI runs reproducible across repeated executions.

## Current rule
A run is considered reproducible if:
- the input values are the same
- the bootstrap count is the same
- the confidence level is the same
- the seed is the same

## Example
If I run:

- values = [0.72, 0.81, 0.77, 0.69, 0.85]
- n_bootstrap = 1000
- confidence_level = 0.95
- seed = 42

I should get the same output each time.

## Why seed matters
Bootstrap sampling uses randomness. Without a fixed seed, repeated runs can produce slightly different results.

## Current implementation
The bootstrap CI utility uses `random.Random(seed)` so that repeated runs with the same seed are deterministic.

## Future extensions
- save run config automatically
- log seed and config in output
- add run IDs