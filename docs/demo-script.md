# Demo Script

## 1. Install And Verify

```bash
python3 -m pip install -r requirements.txt
python3 scripts/verify_dependencies.py
python3 -m pytest
ruff check .
```

## 2. Start The API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open the dashboard:

```text
http://127.0.0.1:8000/
```

## 3. API Smoke Checks

Health:

```bash
curl http://127.0.0.1:8000/health
```

Sample analysis:

```bash
curl http://127.0.0.1:8000/analysis/sample
```

Upload analysis:

```bash
curl -X POST "http://127.0.0.1:8000/analysis/upload" \
  -F "file=@data/sample/sales_sample.csv"
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

## 4. Dashboard Walkthrough

1. Open `http://127.0.0.1:8000/`.
2. Click `Analyze Sample Data`.
3. Start with the Executive Summary panel: revenue, orders, anomalies, confidence, forecast readiness, recommendations, and workflow counts.
4. Explain the Quality Gate status card: whether the analysis is pass, warning, or blocked and whether human review is needed.
5. Explain the Forecast Readiness card: readiness status, confidence level, and next forecast period.
6. Review the top Business Actions: high-priority recommendations first, with owner roles, expected impact, and follow-up metrics.
7. Explain the Forecast and Trend Snapshot: revenue/order baselines, forecast warnings, and trend directions.
8. Explain Visual Analytics as evidence: each chart has a business question, interpretation, related insights, and recommended actions.
9. Expand Technical Evidence only when needed for reviewers: validation, profile, quality score, preparation, lineage, KPIs, anomalies, workflows, audit events, and raw JSON.
10. Upload `data/sample/sales_sample.csv` and show the same response contract with the same stakeholder-first layout.

## 5. Artifact And Operations Talking Points

- Markdown and PDF reports can be generated from `AnalysisResponse`.
- PNG chart artifacts can be generated from chart-ready data.
- Visual analytics connect charts to business questions, interpretations, insight IDs, and stakeholder actions.
- Trend analysis summarizes historical monthly movement without forecasting.
- Baseline forecasts use readiness checks, last-period values, moving averages, and simple trend projection without ML.
- Quality gate decisions prevent low-quality data from becoming confident executive output.
- Recommendations and workflow improvements move the platform from analytics to business action.
- Data profile and quality score improve analytics credibility before deeper statistical modeling.
- Source metadata, preparation, lineage, and manipulation summaries make the pipeline end-to-end analytics rather than only KPI reporting.
- CI runs dependency verification, Ruff, and pytest.
- Deployment is ready with Dockerfile, runtime config, and `docs/deployment.md`.
