# InsightOps-AI
InsightOps-AI is an AI-powered sales analytics automation platform that ingests sales data, validates it, computes KPIs, detects anomalies, generates charts, and produces executive-ready insights with auditability.

## Current Capabilities

- FastAPI health check endpoint.
- CSV loading for sample sales data.
- Row-level sales data validation with structured error reporting.
- Deterministic KPI computation from valid sales records.
- Security guardrails for prompt-injection style text in sales fields.
- Audit events for the main analysis pipeline steps.
- Deterministic sales anomaly detection.
- Chart-ready data generation without visual rendering.
- Deterministic executive insight generation from validation, KPI, security, and anomaly outputs.
- Sample analysis API that returns validation, KPI, security, anomaly, chart, insight, and audit outputs.

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
- `security`: prompt-injection scan status, flagged fields, and human review status.
- `anomalies`: deterministic anomaly count and anomaly details.
- `charts`: chart-ready bar chart series for revenue and anomaly severity.
- `insights`: deterministic executive summary, insight list, and recommended actions.
- `audit_events`: deterministic audit trail events for the analysis run.

## Analysis Pipeline

`GET /analysis/sample` runs the sample sales data through this deterministic pipeline:

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

The project intentionally keeps business logic deterministic before adding LLM behavior.

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
    detector.py
  insights/
    generator.py
  charts/
    chart_data.py
  security/
    policy.py
    prompt_injection.py
  audit/
    events.py

tests/
```

## Documentation Practice

As each sprint adds or changes behavior, update this README in the same pass as the code. Documentation should stay current with:

- API endpoints and response sections.
- New domain modules and their purpose.
- Deterministic business rules.
- Test and lint commands.
- Features that are intentionally not implemented yet.

Not implemented yet:

- LLM-generated executive insights. Current insights are deterministic rules.
- Visual chart rendering.
- Frontend or dashboard code.

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
