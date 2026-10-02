# Run persistence and reproducibility

Status: local completed-run artifacts implemented; database and asynchronous state
machines are future designs.

The CLI writes a run directory through temporary staging and a per-run exclusive
lock. An existing run ID is rejected; the API intentionally remains stateless.

| File | Contents |
|---|---|
| `request.json` | Canonical inputs, IDs, provenance, configuration |
| `results.json` | Per-example scores, slices, uncertainties, flags, decision |
| `report.md` | Human-readable report derived from those results |
| `workflow_demos.json` | Separate synthetic demonstrations: judge/calibration, independent A/B, retrieval evaluation, failure analysis, and practical-vs-statistical significance |
| `manifest.json` | Status, UTC timestamp, hashes, source fingerprints, runtime versions |

Request hashes cover all request fields; dataset hashes cover identities and
supplied examples/outputs, excluding run ID and evaluator configuration.
Dependency/source fingerprints support tracing the execution environment. They
are not cryptographic signatures or an authenticity guarantee.

Deterministic result and report bytes can be reproduced with the same source,
inputs, configuration, and pinned runtime. Timestamps differ by design. Live model
regeneration is not implemented and is not promised to be deterministic.

`verify_run` detects modified artifacts and inconsistent request/run identifiers.
The local writer avoids silent overwrites among cooperating processes. A hard crash
may leave a lock or staging directory; inspect these before removing them. This is
not a crash-durable transactional database or protection against malicious writers.

## Production design

Use authenticated run ownership, a durable object store plus transactional metadata,
queued/running/completed/failed states, cancellation, idempotency keys, retention,
and recovery policies. Add encryption/access control for sensitive model data.
Those controls are not implemented in this local prototype.