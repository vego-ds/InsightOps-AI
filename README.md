# InsightOps-AI

InsightOps-AI is a production-style sales analytics automation API. It loads sample sales data, validates rows, computes KPIs, scans for security risks, detects anomalies, prepares chart-ready data, generates deterministic executive insights, and returns an auditable analysis payload.

## API Endpoints

Interactive API docs are available at `/docs` when the API is running. OpenAPI JSON is available at `/openapi.json`.

### GET /health

Returns:

```json
{
  "status": "ok",
  "service": "insightops-ai"
}
```

### GET /analysis/sample

Runs `data/sample/sales_sample.csv` through the analysis pipeline and returns:

- `validation`
- `kpis`
- `security`
- `anomalies`
- `charts`
- `insights`
- `audit_events`

The analysis API uses a typed response contract for these sections so sample and upload analysis return the same schema.

### POST /analysis/upload

Accepts a user-provided `.csv` file, up to 1 MB, and returns the same analysis sections:

- `validation`
- `kpis`
- `security`
- `anomalies`
- `charts`
- `insights`
- `audit_events`

Example:

```bash
curl -X POST "http://127.0.0.1:8000/analysis/upload" \
  -F "file=@data/sample/sales_sample.csv"
```

Upload errors:

- `400` for invalid or empty files.
- `413` for oversized files.

## Pipeline

```text
CSV load
  -> row validation
  -> security scan
  -> KPI computation
  -> anomaly detection
  -> chart data generation
  -> executive insight generation
  -> audit event generation
```

The project keeps business logic deterministic before adding any LLM behavior.

## Project Structure

```text
app/                         FastAPI entrypoint
data/sample/                 Sample sales CSV
insightops/ingestion/        CSV loading
insightops/validation/       Sales record validation and reports
insightops/metrics/          KPI computation
insightops/security/         Prompt-injection guardrails
insightops/anomalies/        Deterministic anomaly detection
insightops/charts/           Chart-ready data structures
insightops/insights/         Deterministic executive insights
insightops/audit/            Audit event models
insightops/pipeline/         Analysis orchestration
tests/                       Pytest suite
```

## Local Development

Run the API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Run tests:

```bash
python3 -m pytest
```

Run linting:

```bash
ruff check .
```

## CI and Environment

- CI runs on GitHub Actions with Python 3.12.
- CI verifies dependencies with `python3 scripts/verify_dependencies.py`.
- CI runs `ruff check .` and `python3 -m pytest`.
- Local development should use the same test and lint commands.

## Chart Artifacts

The backend can generate deterministic PNG chart artifacts from chart-ready data. Frontend/dashboard rendering is intentionally not added yet.

## Report Artifacts

The backend can generate deterministic Markdown executive report artifacts from analysis outputs. PDF generation and dashboard rendering are intentionally not added yet.

## Not Implemented Yet

- LLM-generated insights.
- Visual chart rendering.
- PDF generation.
- Frontend or dashboard code.
