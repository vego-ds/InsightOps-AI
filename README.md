# InsightOps-AI
InsightOps-AI is an AI-powered sales analytics automation platform that ingests sales data, validates it, computes KPIs, detects anomalies, generates charts, and produces executive-ready insights with auditability.

## Current Capabilities

- FastAPI health check endpoint.
- CSV loading for sample sales data.
- Row-level sales data validation with structured error reporting.
- Deterministic KPI computation from valid sales records.
- Sample analysis API that returns validation results and KPI metrics.

## API Endpoints

### GET /health

Returns service health:

```json
{
  "status": "ok",
  "service": "insightops-ai"
}
```

### GET /analysis/sample

Loads `data/sample/sales_sample.csv`, validates all rows, computes KPIs from valid records, and returns:

- `validation`: total rows, valid rows, invalid rows, and row-level errors.
- `kpis`: total revenue, total orders, total units sold, average order value, and grouped revenue by region, product, and sales rep.

## Project Structure

```text
app/
  main.py

data/
  sample/
    sales_sample.csv

insightops/
  ingestion/
    csv_loader.py
  validation/
    models.py
    report.py
  metrics/
    kpis.py
  anomalies/
  insights/
  charts/
  audit/

tests/
```

## Local Development

Install dependencies, then run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Run tests and linting:

```bash
python3 -m pytest
ruff check .
```
