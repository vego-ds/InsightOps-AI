# InsightOps-AI

InsightOps-AI is a production-style sales analytics automation API. It loads sample sales data, validates rows, computes KPIs, scans for security risks, detects anomalies, prepares chart-ready data, generates deterministic executive insights, and returns an auditable analysis payload.

## API Endpoints

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

## Not Implemented Yet

- LLM-generated insights.
- Visual chart rendering.
- Frontend or dashboard code.
