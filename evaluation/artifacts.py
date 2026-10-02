"""Local run artifacts with hashes, source provenance, and no silent overwrite."""
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
import hashlib
import json
import os
import platform
import shutil
import tempfile

from evaluation.contracts import EvaluationRequest
from evaluation.pipeline import canonical_json, canonical_request, digest


def source_fingerprint():
    root = Path(__file__).resolve().parents[1]
    files = sorted(path for folder in ("evaluation", "app", "examples")
                   for path in (root / folder).rglob("*.py"))
    hashes = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in files}
    return {"sha256": digest(hashes), "files": hashes}


def save_run(request: EvaluationRequest, result: dict, report: str, output_root: Path,
             supplements: dict | None = None) -> Path:
    """Publish a complete local directory; existing run IDs are never overwritten.

    A per-run lock prevents collisions between cooperating local writers.
    Timestamps live in manifest.json; deterministic outputs are separate.
    """
    payload = canonical_request(request)
    if result["request_sha256"] != digest(payload) or result["run_id"] != request.run_id:
        raise ValueError("Result does not belong to this request.")
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    final = output_root / request.run_id
    lock = output_root / ("." + request.run_id + ".lock")
    # Exclusive creation; a crashed process may leave a lock for manual inspection.
    handle = lock.open("x")
    stage = None
    try:
        handle.close()
        if final.exists():
            raise FileExistsError(f"Run already exists: {final}")
        stage = Path(tempfile.mkdtemp(prefix=".evaluation-", dir=output_root))
        contents = {"request.json": canonical_json(payload),
                    "results.json": canonical_json(result), "report.md": report}
        if supplements is not None:
            contents["workflow_demos.json"] = canonical_json(supplements)
        for name, content in contents.items():
            (stage / name).write_text(content, encoding="utf-8")
        manifest = dict(
            status="completed", run_id=request.run_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            request_sha256=result["request_sha256"], dataset_sha256=result["dataset_sha256"],
            pipeline_version=result["pipeline_version"], python=platform.python_version(),
            dependencies={name: version(name) for name in ("numpy", "pydantic", "fastapi", "PyYAML")},
            source=source_fingerprint(),
            files={name: hashlib.sha256((stage / name).read_bytes()).hexdigest() for name in contents},
        )
        (stage / "manifest.json").write_text(canonical_json(manifest), encoding="utf-8")
        os.rename(stage, final)
        stage = None
        return final
    finally:
        if stage is not None:
            shutil.rmtree(stage)
        lock.unlink(missing_ok=True)


def verify_run(directory: Path):
    """Detect accidental content changes. Hashes do not provide signed authenticity."""
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    required = {"request.json", "results.json", "report.md"}
    if manifest.get("status") != "completed" or not required <= set(manifest["files"]):
        raise ValueError("Incomplete run manifest.")
    for name, expected in manifest["files"].items():
        if Path(name).name != name or name in {".", ".."}:
            raise ValueError("Invalid artifact path in manifest.")
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Artifact hash mismatch: {name}")
    payload = json.loads((directory / "request.json").read_text(encoding="utf-8"))
    result = json.loads((directory / "results.json").read_text(encoding="utf-8"))
    request = EvaluationRequest.model_validate(payload)
    request_hash = digest(canonical_request(request))
    if request_hash != manifest["request_sha256"] or request_hash != result["request_sha256"]:
        raise ValueError("Request hash mismatch.")
    if request.run_id != result["run_id"] or request.run_id != manifest["run_id"]:
        raise ValueError("Run ID mismatch.")
    return manifest