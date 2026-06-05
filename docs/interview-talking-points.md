# Interview Talking Points

## 30-Second Pitch

InsightOps-AI is a production-style sales analytics automation API. It ingests CSV sales data, validates rows, computes KPIs, detects security risks and anomalies, generates deterministic executive insights, and produces audit-ready outputs, reports, and a lightweight demo dashboard.

## 2-Minute Technical Explanation

The system is built around a deterministic pipeline. FastAPI handles routing, while `insightops/pipeline` orchestrates CSV ingestion, Pydantic validation, security scanning, KPI computation, anomaly detection, chart data generation, executive insight generation, and audit events. The API uses typed response contracts so sample analysis and upload analysis return the same schema. Artifact modules generate PNG charts, Markdown reports, and PDF reports separately, which avoids mixing storage and file delivery decisions into the core API.

## Architecture Talking Points

- `app/main.py` is intentionally thin.
- Domain modules own business logic.
- Pydantic models define inputs, outputs, and API contracts.
- The pipeline returns a stable `AnalysisResponse`.
- Artifact generation is separate from API responses.

## Security Talking Points

- CSV uploads are limited to `.csv` files.
- Upload size defaults to 1 MB and is configurable.
- Suspicious prompt-injection style text is detected.
- Security findings can require human review.
- LLM narrative usage is blocked when prompt injection or human review is detected.

## Data Validation Talking Points

- `SalesRecord` validates schema and business rules.
- Invalid rows do not crash ingestion.
- Validation reports separate valid records from errors.
- KPIs are computed only from valid records.

## Auditability Talking Points

- Each major pipeline stage can emit audit events.
- Validation, KPI, security, anomaly, chart data, and insight stages are traceable.
- Report generation has explicit artifact metadata.

## Testing And CI Talking Points

- Pytest covers API routes, pipeline behavior, validation, KPIs, security, anomalies, charts, reports, narrative safety, and dependency verification.
- Ruff enforces linting.
- GitHub Actions runs dependency verification, Ruff, and pytest on Python 3.12.

## Deployment Talking Points

- Runtime config is environment-driven.
- Dockerfile uses `python:3.12-slim`.
- Deployment guide includes Render, Fly.io, Railway-style commands.
- Health check is `/health`.

## LLM Safety Talking Points

- The LLM layer is optional and disabled by default.
- Deterministic fallback is always available.
- LLMs cannot control pipeline decisions.
- Guarded prompts separate trusted instructions from untrusted data.

## Tradeoffs Made

- No database yet, keeping the demo focused on deterministic analytics.
- No authentication yet, so it is not a production multi-user system.
- Chart visuals are generated as backend PNG artifacts, while the dashboard shows chart data tables.
- Report artifacts are module-level functions, not API downloads yet.

## What I Would Improve Next

- Add authenticated artifact download endpoints.
- Persist audit logs and analysis runs.
- Add user/project scoping.
- Add visual chart rendering to the dashboard.
- Add a real LLM provider behind the existing guardrails.

## Likely Questions

**Why deterministic first?**  
Because validation, metrics, security, and audit outputs need to be explainable before any generative layer is added.

**What does the LLM do?**  
Currently nothing external. The foundation exists, but only deterministic fallback is implemented. A future LLM would only rewrite verified facts.

**How do you prevent bad uploaded data from becoming instructions?**  
Prompt-injection style phrases are scanned, suspicious records trigger review, and prompt builders label source data as untrusted.

**Is this production-ready?**  
It is production-style and deployment-ready for a demo. It still needs authentication, persistence, and stronger multi-user controls for production.
