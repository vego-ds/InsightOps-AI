# InsightOps-AI

InsightOps-AI is a production-style sales analytics automation platform. It collects source metadata, validates sales CSV data, prepares analysis-ready records, computes KPIs, scans for security risks, detects anomalies, prepares chart/report artifacts, and returns typed audit-ready analysis responses.

## Key Capabilities

- CSV ingestion with row-level validation.
- Data collection metadata and transformation lineage.
- Data preparation with deterministic derived analytical fields.
- Data profiling and quality scoring foundation.
- Data quality gate with pass, warning, and blocked governance status.
- Manipulation summaries for monthly revenue, rankings, and discount behavior.
- Monthly trend analysis for revenue, order volume, units sold, average order value, and discount behavior.
- Forecast readiness checks and deterministic baseline forecasts for planning.
- KPI computation from valid records.
- Prompt-injection guardrails and human-review flags.
- Deterministic anomaly detection.
- Visual analytics that pair chart data with business questions, interpretations, related insight IDs, and recommended actions.
- Chart-ready data plus backend PNG chart artifacts.
- Rule-based and statistical IQR outlier detection, including product-relative revenue outliers.
- Deterministic executive insights.
- Business recommendations with evidence, owner roles, expected impact, and follow-up metrics.
- Workflow improvement plans that translate findings into operational process changes.
- Markdown and PDF report artifact generation.
- Optional guarded narrative writer foundation, disabled by default.
- Lightweight static dashboard demo.
- CI, Dockerfile, runtime config, and deployment guide.

## Architecture Overview

```text
FastAPI routes
  -> analysis pipeline
  -> collection / validation / profiling / quality gate
  -> preparation / manipulation / trends / baseline forecasts / KPIs / anomalies
  -> insights / visual analytics / recommendations / audit events
  -> typed API response
```

`app/main.py` stays thin. Business logic lives in `insightops/` modules, and detailed design notes live in [docs/system-design.md](docs/system-design.md).

## API Endpoints

- `GET /`: lightweight static dashboard.
- `GET /health`: service health.
- `GET /analysis/sample`: analyze bundled sample CSV.
- `POST /analysis/upload`: analyze uploaded `.csv` files up to 100 MB.
- `POST /analysis/sample/report`: download sample analysis report.
- `POST /analysis/upload/report`: download uploaded CSV analysis report.
- `GET /docs`: interactive API docs.
- `GET /openapi.json`: OpenAPI schema.

Both analysis endpoints return:

- `source_metadata`
- `validation`
- `data_profile`
- `quality_score`
- `quality_gate`
- `preparation`
- `transformation_log`
- `manipulation_summary`
- `trend_analysis`
- `forecast_analysis`
- `kpis`
- `security`
- `anomalies`
- `charts`
- `insights`
- `recommendation_plan`
- `workflow_improvement_plan`
- `audit_events`

Phase 2 analytics depth now makes the data lifecycle explicit. Source metadata
captures collection context, preparation creates deterministic derived fields,
transformation lineage explains what changed, manipulation summaries expose
monthly revenue, ranked entities, and discount behavior, trend analysis summarizes
time-based business performance, baseline forecasting provides deterministic
last-period, moving-average, and trend-projection planning aids, and quality scoring
returns a deterministic 0-100 score with issues and recommendations.
Visual analytics now make charts evidence objects: outputs explain the business
question, interpretation, and recommendation linkage behind each chart.
The quality gate assigns analysis confidence and makes sure low-quality data
does not silently become confident executive output.
The recommendation engine turns analytics into stakeholder-ready action plans
and workflow improvements.

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

## CSV Schema Compatibility And Mapping

InsightOps-AI enforces strict schema verification on uploaded CSV files to guarantee data governance and prevent processing failures:

- **Canonical Sales Schema**: The governed pipeline expects:
  - `order_id`, `order_date`, `customer_id`, `region`, `product`, `sales_rep`, `quantity`, `unit_price`, `discount`, `revenue`.
- **Header Normalization**: Headers are automatically trimmed, lowercased, spaces replaced with underscores, and punctuation removed.
- **Supported Schema Mapping (`classic_sales_sample`)**: External schemas matching classic sample layouts are automatically mapped to canonical fields (e.g., `ORDERNUMBER` -> `order_id`, first and last names concatenated into `sales_rep`, and `discount` defaulted to `0` with a warning).
- **Upload Preview**: The `POST /analysis/upload/preview` endpoint allows inspecting headers, detecting schemas, listing missing columns, and checking compatibility without executing full analysis.
- **Supported Encodings**: While UTF-8 and UTF-8 BOM are recommended for best compatibility, the application also safely supports common legacy encodings like Windows-1252 (cp1252) and ISO-8859-1. Legacy encodings trigger warning messages in the preview panel. Truly unreadable or binary-like files will return a controlled HTTP 400.
- **100 MB Limit**: Max upload size limit is strictly set to 100 MB (104,857,600 bytes).

## Security And Guardrails

InsightOps-AI keeps deterministic logic as the source of truth. Uploaded files are CSV-only, size-limited, validated row by row, scanned for prompt-injection style text, and routed through typed response contracts.

The optional narrative layer defaults to disabled mode and requires no API key. OpenRouter can be enabled explicitly with `INSIGHTOPS_NARRATIVE_PROVIDER=openrouter` and `INSIGHTOPS_OPENROUTER_API_KEY`. Optional settings are `INSIGHTOPS_OPENROUTER_MODEL=openrouter/auto` and `INSIGHTOPS_OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`. OpenRouter is only used for narrative writing; it never controls pipeline decisions, and deterministic fallback remains available.

## Artifacts

- PNG chart artifacts can be generated from chart-ready data.
- Markdown and PDF executive reports can be exported through report endpoints.
- Supported report export formats are `pdf`, `markdown`, and `md`.
- Report exports use temporary per-request files and do not persist uploaded user data or generated reports in the repository.

## Forecasting

Forecasting is deterministic and baseline-only. The platform checks forecast
readiness, then calculates last-period, moving-average, and simple trend
projection baselines. These outputs are planning aids, not ML predictions,
regression, or advanced forecasting models.

## Dashboard

The dashboard is a governed sales analytics workspace built with vanilla HTML, CSS, and JavaScript. It features:
* **Ask Guided Analytics**: A client-side deterministic command router supporting synonym grouping, auto-scrolling, brief card highlights, and report triggers. No `eval` or arbitrary code execution is performed, maintaining full security.
* **Dynamic Suggestion Chips**: State-aware action buttons that adapt based on whether a dataset has been analyzed.
* **No-Library Visual Analytics**: Fully responsive, dependency-free visualizations rendered via CSS bar gauges, inline SVG line charts, donut/pie charts, and half-donut metric gauges, with interactive live search and category filtering controls.
* **Technical Evidence Drawer**: Collapsible sections for all underlying API fields, protected by a centralized render error guard and featuring an automatic validation diagnostics shape checker.

It does not use external frontend frameworks (React, Vue, etc.) or visual libraries (Chart.js, D3.js).

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
- [Application overview](docs/application-overview.md)
- [Threat model](docs/threat-model.md)
- [Deployment guide](docs/deployment.md)
- [Portfolio summary](docs/portfolio-summary.md)
