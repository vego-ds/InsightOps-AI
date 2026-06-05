# Threat Model

## Assets Protected

- Sales data.
- Uploaded files.
- Analysis outputs.
- Generated reports.
- API availability.
- Future LLM boundaries.

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
- LLM hallucination if future providers are added.

## Mitigations Implemented

- CSV-only upload checks.
- 1 MB default upload size limit.
- Row-level validation with Pydantic.
- Prompt-injection phrase detection.
- Human-review flags.
- Deterministic fallback for narrative generation.
- Typed API contracts.
- Audit events.
- `.gitignore` and `.dockerignore` for cache, env, and generated files.
- Dependency verification script.
- CI with dependency verification, Ruff, and pytest.

## Remaining Risks

- No authentication or authorization.
- No database-backed audit persistence.
- No artifact access control.
- Prompt-injection detection is phrase-based and conservative.
- Dependency versions are not pinned.
- No real LLM provider is integrated yet, so future provider work will need additional security review.

## Future Mitigations

- Add authentication and authorization.
- Store audit events in a durable system.
- Add artifact retention and access policies.
- Pin dependencies or add lockfile workflow.
- Add file content scanning beyond extension checks.
- Add provider-specific LLM safety tests before enabling real LLM calls.
