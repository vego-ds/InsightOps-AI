# InsightOps-AI

InsightOps-AI is a production-style sales analytics automation platform. It validates sales CSV data, computes KPIs, scans for security risks, detects anomalies, prepares chart/report artifacts, and returns typed audit-ready analysis responses.

## Key Capabilities

- CSV ingestion with row-level validation.
- KPI computation from valid records.
- Prompt-injection guardrails and human-review flags.
- Deterministic anomaly detection.
- Chart-ready data plus backend PNG chart artifacts.
- Deterministic executive insights.
- Markdown and PDF report artifact generation.
- Optional guarded narrative writer foundation, disabled by default.
- Lightweight static dashboard demo.
- CI, Dockerfile, runtime config, and deployment guide.

## Architecture Overview

```text
FastAPI routes
  -> analysis pipeline
  -> validation / security / KPIs / anomalies
  -> chart data / insights / audit events
  -> typed API response
```

`app/main.py` stays thin. Business logic lives in `insightops/` modules, and detailed design notes live in [docs/system-design.md](docs/system-design.md).

## API Endpoints

- `GET /`: lightweight static dashboard.
- `GET /health`: service health.
- `GET /analysis/sample`: analyze bundled sample CSV.
- `POST /analysis/upload`: analyze uploaded `.csv` files up to 1 MB.
- `GET /docs`: interactive API docs.
- `GET /openapi.json`: OpenAPI schema.

Both analysis endpoints return:

- `validation`
- `kpis`
- `security`
- `anomalies`
- `charts`
- `insights`
- `audit_events`

## Quickstart

```bash
python3 -m pip install -r requirements.txt
python3 scripts/verify_dependencies.py
python3 -m pytest
ruff check .
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open the dashboard:

```text
http://127.0.0.1:8000/
```

Upload example:

```bash
curl -X POST "http://127.0.0.1:8000/analysis/upload" \
  -F "file=@data/sample/sales_sample.csv"
```

## Security And Guardrails

InsightOps-AI keeps deterministic logic as the source of truth. Uploaded files are CSV-only, size-limited, validated row by row, scanned for prompt-injection style text, and routed through typed response contracts. The optional narrative layer has deterministic fallback and does not call external LLM providers.

## Artifacts

- PNG chart artifacts can be generated from chart-ready data.
- Markdown executive reports can be generated from analysis outputs.
- PDF executive reports can be generated from analysis outputs.
- Artifact generation is currently module-level and not exposed through API download endpoints.

## Dashboard

The dashboard is a lightweight static demo UI built with HTML, CSS, and vanilla JavaScript. It can run sample analysis, upload CSV files, and render response sections as readable summaries and tables. It is not a production frontend.

## CI And Deployment

GitHub Actions runs dependency verification, Ruff, and pytest on Python 3.12. The project includes a Dockerfile, runtime config, and [deployment guide](docs/deployment.md).

## Screenshots

- Dashboard home: placeholder.
- Sample analysis result: placeholder.
- CSV upload flow: placeholder.
- OpenAPI docs: placeholder.
- Generated report artifact: placeholder.

## Documentation

- [System design](docs/system-design.md)
- [Demo script](docs/demo-script.md)
- [Interview talking points](docs/interview-talking-points.md)
- [Threat model](docs/threat-model.md)
- [Deployment guide](docs/deployment.md)
- [Portfolio summary](docs/portfolio-summary.md)
