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
3. Explain validation results: total, valid, invalid rows, and row-level errors.
4. Explain KPI results: revenue, order count, units sold, average order value.
5. Explain security guardrails: prompt-injection detection and human-review flags.
6. Explain anomaly detection: deterministic thresholds for revenue, quantity, discount, and zero revenue.
7. Explain chart data: dashboard shows chart-ready data as tables, not visual charts.
8. Explain executive insights and recommended actions.
9. Upload `data/sample/sales_sample.csv` and show the same response contract.

## 5. Artifact And Operations Talking Points

- Markdown and PDF reports can be generated from `AnalysisResponse`.
- PNG chart artifacts can be generated from chart-ready data.
- CI runs dependency verification, Ruff, and pytest.
- Deployment is ready with Dockerfile, runtime config, and `docs/deployment.md`.
