"""Authored synthetic responses. No actual model generated these examples.

The scenarios are intentionally constructed to exercise overall gains, a
regressing slice, lexical/semantic disagreement, and metric blind spots.
"""
from evaluation.contracts import EvaluationRequest
from evaluation.pipeline import canonical_json

# slice, reference, authored baseline, authored challenger
CASES = [
    ("support", "contact support to reset your password", "contact support", "contact support to reset your password"),
    ("support", "request a refund for the delayed package", "delayed package", "request a refund for the delayed package"),
    ("support", "cancel the order before the shipment", "cancel order", "cancel the order before the shipment"),
    ("support", "recover your account with the backup passcode", "recover account", "recover your account with the backup passcode"),
    ("support", "email support before you delete the account", "email support", "email support before you delete the account"),
    ("support", "the delayed parcel qualifies for a refund", "parcel refund", "the delayed parcel qualifies for a refund"),
    ("support", "restore your profile then reset the password", "restore profile", "restore your profile then reset the password"),
    ("support", "contact support if the reimbursement is delayed", "contact support", "contact support if the reimbursement is delayed"),
    ("transport", "buy a fast car", "car", "purchase a quick automobile"),
    ("transport", "the vehicle is safe", "vehicle", "the vehicle is secure"),
    ("transport", "the package is delayed", "package", "the parcel is delayed"),
    ("transport", "contact support for the shipment", "shipment", "contact support for the parcel"),
    ("transport", "purchase the car before the trip", "purchase car", "purchase the car before the trip"),
    ("transport", "the rapid vehicle needs a repair", "vehicle", "the rapid vehicle needs a repair"),
    ("transport", "cancel the shipment and request a refund", "cancel shipment", "cancel the shipment and request a refund"),
    ("transport", "the safe automobile is ready for purchase", "automobile", "the safe automobile is ready for purchase"),
    ("technical", "encrypt data before you save the backup", "encrypt data before you save the backup", "save data"),
    ("technical", "restore the backup before deleting the records", "restore the backup before deleting the records", "delete records"),
    ("technical", "reset the password after an account error", "reset the password after an account error", "account error"),
    ("technical", "store the encryption credential in a secure location", "store the encryption credential in a secure location", "store credential"),
    ("technical", "contact support before removing the backup", "contact support before removing the backup", "remove backup"),
    ("technical", "save a copy before you erase the data", "save a copy before you erase the data", "erase data"),
    ("technical", "the backup is safe", "the backup is safe", "the backup is not safe"),
    ("technical", "encryption protects the stored information", "encryption protects the stored information", "store information"),
]


def make_demo_request() -> EvaluationRequest:
    examples, baseline, challenger = [], [], []
    for index, (label, reference, a, b) in enumerate(CASES, start=1):
        example_id = f"ex-{index:03d}"
        examples.append(dict(example_id=example_id,
                             prompt=f"Provide the following fixture instruction accurately: {reference}",
                             reference_response=reference, slice=label))
        baseline.append(dict(example_id=example_id, response=a))
        challenger.append(dict(example_id=example_id, response=b))
    return EvaluationRequest(
        run_id="portfolio-demo-v1", dataset_name="authored-evaluation-fixtures",
        dataset_version="1.0", data_kind="synthetic",
        provenance="Authored synthetic examples for software demonstration; no model or human evaluation study.",
        baseline_name="authored-baseline-fixture", challenger_name="authored-challenger-fixture",
        examples=examples, baseline=baseline, challenger=challenger,
    )


if __name__ == "__main__":
    print(canonical_json(make_demo_request().model_dump()), end="")