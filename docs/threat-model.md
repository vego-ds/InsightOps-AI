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
- OpenRouter API key exposure.
- External provider outage or malformed response.

## Mitigations Implemented

- CSV-only upload checks.
- 1 MB default upload size limit.
- Row-level validation with Pydantic.
- Prompt-injection phrase detection.
- Human-review flags.
- Deterministic fallback for narrative generation.
- OpenRouter credentials are environment-only and optional.
- Provider errors and malformed responses fall back deterministically.
- Prompt-injection and human-review cases block LLM provider calls.
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
- OpenRouter narrative output can still be stylistically wrong or overconfident, so deterministic evidence remains the source of truth.

## Future Mitigations

- Add authentication and authorization.
- Store audit events in a durable system.
- Add artifact retention and access policies.
- Pin dependencies or add lockfile workflow.
- Add file content scanning beyond extension checks.
- Add provider-specific monitoring and evaluation before relying on LLM narratives in production.
