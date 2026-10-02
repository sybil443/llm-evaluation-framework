import pytest

from evaluation.rubric_schema import calculate_weighted_score, load_rubric_schema_yaml


@pytest.fixture
def rubric():
    return load_rubric_schema_yaml()


def _scores(rubric, value):
    return {criterion.name: value for criterion in rubric.criteria}


def test_calculate_weighted_score_returns_expected_value(rubric) -> None:
    scores = {
        "correctness": 4,
        "relevance": 5,
        "completeness": 3,
        "clarity": 4,
        "safety": 5,
    }

    assert calculate_weighted_score(rubric, scores) == pytest.approx(0.7875)


def test_calculate_weighted_score_at_min_mid_and_max(rubric) -> None:
    assert calculate_weighted_score(rubric, _scores(rubric, 1)) == pytest.approx(0.0)
    assert calculate_weighted_score(rubric, _scores(rubric, 3)) == pytest.approx(0.5)
    assert calculate_weighted_score(rubric, _scores(rubric, 5)) == pytest.approx(1.0)


def test_calculate_weighted_score_raises_for_missing_criterion(rubric) -> None:
    scores = _scores(rubric, 4)
    del scores["safety"]

    with pytest.raises(ValueError, match="missing required criteria"):
        calculate_weighted_score(rubric, scores)


def test_calculate_weighted_score_raises_for_unknown_criterion(rubric) -> None:
    scores = _scores(rubric, 4)
    scores["fluency"] = 4

    with pytest.raises(ValueError, match="unknown criteria"):
        calculate_weighted_score(rubric, scores)


def test_calculate_weighted_score_raises_for_score_below_min(rubric) -> None:
    scores = _scores(rubric, 4)
    scores["correctness"] = 0

    with pytest.raises(ValueError, match="correctness"):
        calculate_weighted_score(rubric, scores)


def test_calculate_weighted_score_raises_for_score_above_max(rubric) -> None:
    scores = _scores(rubric, 4)
    scores["safety"] = 6

    with pytest.raises(ValueError, match="safety"):
        calculate_weighted_score(rubric, scores)


@pytest.mark.parametrize("bad", [True, float("nan"), float("inf"), "4"])
def test_calculate_weighted_score_rejects_non_numeric_scores(rubric, bad) -> None:
    scores = _scores(rubric, 4)
    scores["clarity"] = bad

    with pytest.raises(ValueError, match="clarity"):
        calculate_weighted_score(rubric, scores)