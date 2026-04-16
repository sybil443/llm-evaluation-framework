import pytest

from evaluation.bootstrap_ci import bootstrap_mean_ci

def test_bootstrap_mean_ci_returns_correct_result() -> None:
    result = bootstrap_mean_ci([1.0,2.0,3.0,4.0,5.0], num_bootstrap=1000, confidence_level=0.95, seed=42)
    
    assert result == {
        "mean": 3.0,
        "ci_lower": 1.8,
        "ci_upper": 4.2,
        "n_bootstrap": 1000,
        "confidence_level": 0.95,
        "original_mean": 3.0,
        "original_n": 5,
    }

def test_bootstrap_mean_ci_return_expected_keys() -> None:
    result = bootstrap_mean_ci([1.0,2.0,3.0,4.0,5.0], num_bootstrap=1000, confidence_level=0.95, seed=42)
    assert set(result.keys()) == {"mean", "ci_lower", "ci_upper", "n_bootstrap", "confidence_level", "original_mean", "original_n"}

def test_bootstrap_mean_ci_raises_value_error_for_empty_input() -> None:
    with pytest.raises(ValueError):
        bootstrap_mean_ci([], num_bootstrap=1000, confidence_level=0.95, seed=42)

def test_bootstrap_mean_ci_raises_value_error_for_negative_bootstrap_count() -> None:
    with pytest.raises(ValueError):
        bootstrap_mean_ci([1.0,2.0,3.0,4.0,5.0], num_bootstrap=-1, confidence_level=0.95, seed=42)

def test_bootstrap_mean_ci_raises_value_error_for_confidence_level_outside_0_1() -> None:
    with pytest.raises(ValueError):
        bootstrap_mean_ci([1.0,2.0,3.0,4.0,5.0], num_bootstrap=1000, confidence_level=1.01, seed=42)
    with pytest.raises(ValueError):
        bootstrap_mean_ci([1.0,2.0,3.0,4.0,5.0], num_bootstrap=1000, confidence_level=-0.01, seed=42)
