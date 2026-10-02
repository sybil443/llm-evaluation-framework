from evaluation.statistics import bootstrap_summary


def test_bootstrap_summary_is_reproducible_with_same_seed() -> None:
    values = [0.72, 0.81, 0.77, 0.69, 0.85]

    result_1 = bootstrap_summary(
        values,
        n_resamples=1000,
        confidence_level=0.95,
        seed=42,
    )
    result_2 = bootstrap_summary(
        values,
        n_resamples=1000,
        confidence_level=0.95,
        seed=42,
    )

    assert result_1 == result_2