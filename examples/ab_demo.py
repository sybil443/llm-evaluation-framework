"""Independent-group A/B example; never used for same-prompt paired data."""
from dataclasses import asdict
from evaluation.ab_testing import two_proportion_z_test


def run_ab_demo():
    counts = dict(control_successes=120, control_total=1000,
                  treatment_successes=160, treatment_total=1000)
    result = two_proportion_z_test(**counts)
    return dict(data_kind="synthetic", counts=counts, result=asdict(result),
                assumptions="Independent Bernoulli groups and adequate expected cell counts.",
                limitation="Illustrative counts, not an online experiment or measured product lift.")