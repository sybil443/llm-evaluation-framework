import pytest
from pydantic import ValidationError

from evaluation.contracts import EvaluationRequest
from examples.demo_data import make_demo_request


def test_valid_request_roundtrip():
    original = make_demo_request()
    assert EvaluationRequest.model_validate_json(original.model_dump_json()) == original


@pytest.mark.parametrize("key,value", [
    ("n_bootstrap", 0), ("n_bootstrap", True), ("n_bootstrap", 10001),
    ("confidence_level", float("nan")), ("confidence_level", 1),
    ("minimum_effect", -0.1), ("seed", -1),
])
def test_invalid_config_rejected(key, value):
    payload = make_demo_request().model_dump()
    payload["config"][key] = value
    with pytest.raises(ValidationError):
        EvaluationRequest.model_validate(payload)


@pytest.mark.parametrize("field", ["example_id", "prompt", "reference_response", "slice"])
def test_blank_example_fields_rejected(field):
    payload = make_demo_request().model_dump()
    payload["examples"][0][field] = " "
    with pytest.raises(ValidationError):
        EvaluationRequest.model_validate(payload)


def test_unknown_fields_and_path_traversal_rejected():
    payload = make_demo_request().model_dump()
    payload["run_id"] = "../outside"
    payload["unrecognized_option"] = True
    with pytest.raises(ValidationError):
        EvaluationRequest.model_validate(payload)


def test_missing_reference_rejected_in_reference_based_workflow():
    payload = make_demo_request().model_dump()
    del payload["examples"][0]["reference_response"]
    with pytest.raises(ValidationError):
        EvaluationRequest.model_validate(payload)


def test_response_length_is_bounded_for_lcs_memory():
    payload = make_demo_request().model_dump()
    payload["challenger"][0]["response"] = "word " * 257
    with pytest.raises(ValidationError):
        EvaluationRequest.model_validate(payload)

