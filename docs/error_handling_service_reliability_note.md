# Error handling and service reliability

Status: input validation, operational events, and local artifact errors implemented.

- HTTP 422: malformed request, unknown fields, invalid IDs/configuration, unpaired outputs.
- HTTP 400: validated request encounters a pipeline data-quality/value error.
- HTTP 500: unexpected software errors; they are not disguised as successful evaluations.
- CLI: input, persistence, and execution errors exit nonzero. Successful runs print the report path.
- Data-quality warnings and semantic zero-coverage warnings remain in results and report.
- Failure tags represent review heuristics, not transport/service errors.

Service log messages contain JSON event payloads with run ID, example count,
duration, quality-issue count, decision, or error type. They do not log raw prompts
or responses. The local console formatter may add the logger's level/name prefix;
this is not a deployed observability backend.

Input bounds limit the local demo's work. They are not a full denial-of-service
strategy. Production needs request/body limits, concurrency budgets, job timeouts,
rate limits, authentication, bounded provider retries, health/readiness separation,
and incident handling. The health endpoint currently reports process availability.