from evaluation.ab_compare import compare_mean_delta


def test_compare_mean_delta_returns_expected_keys() -> None:
    result = compare_mean_delta([1.0, 2.0, 3.0], [2.0, 3.0, 4.0], seed=42)

    assert set(result.keys()) == {
        "mean_a",
        "mean_b",
        "delta",
        "ci_a",
        "ci_b",
    }