# Threat Model

## Assets Protected

- Sales data.
- Uploaded files.
- Analysis outputs.
- Generated reports.
- API availability.
- Future LLM boundaries.
- Executive confidence decisions.

## Trust Boundaries

- Uploaded CSV file.
- API layer.
- Deterministic pipeline.
- Optional narrative writer.
- Generated artifacts.

## Threats

- Malicious CSV content.
- Prompt injection text inside uploaded data.
- Oversized uploads.
- Unsupported file types.
- Accidental secrets.
- Dependency drift.
- Report artifact leakage.
- Temporary report file cleanup failure.
- Uploaded data persistence risk.
- Oversized report generation requests.
- LLM hallucination if future providers are added.
- OpenRouter API key exposure.
- External provider outage or malformed response.
- Low-quality data being presented as high-confidence executive output.
- Missing data, duplicate order IDs, or invalid rows causing misleading analysis.

## Mitigations Implemented

- CSV-only upload checks.
- 100 MB default upload size limit with chunked streaming and dynamic size enforcement.
- Row-level validation with Pydantic.
- Prompt-injection phrase detection.
- Human-review flags.
- Deterministic fallback for narrative generation.
- OpenRouter credentials are environment-only and optional.
- Provider errors and malformed responses fall back deterministically.
- Prompt-injection and human-review cases block LLM provider calls.
- Data quality gate assigns pass, warning, or blocked governance status.
- Low-confidence or blocked gate outcomes restrict executive reporting and LLM narrative eligibility.
- Report generation respects the quality gate and blocks reports when report generation is not allowed.
- Report exports use temporary directories and return bytes instead of persistent repository files.
- Uploaded files are streamed to temporary files and guaranteed to be unlinked (deleted) immediately upon request completion (success or error).
- Typed API contracts.
- Audit events.
- `.gitignore` and `.dockerignore` for cache, env, and generated files.
- Dependency verification script.
- CI with dependency verification, Ruff, and pytest.

## Remaining Risks

- No authentication or authorization.
- No database-backed audit persistence.
- No artifact access control.
- No persistent report storage or artifact retention policy.
- Prompt-injection detection is phrase-based and conservative.
- Dependency versions are not pinned.
- OpenRouter narrative output can still be stylistically wrong or overconfident, so deterministic evidence remains the source of truth.
- Low-quality source data can still require human remediation before business use.

## Future Mitigations

- Add authentication and authorization.
- Store audit events in a durable system.
- Add artifact retention and access policies.
- Add authenticated report export access controls before production use.
- Pin dependencies or add lockfile workflow.
- Add file content scanning beyond extension checks.
- Add provider-specific monitoring and evaluation before relying on LLM narratives in production.
- Persist quality gate decisions for governance review.
