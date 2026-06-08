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
2. Observe the state-aware command suggestion chips (e.g. *Run sample analysis*).
3. Click `Analyze Sample Data` (or the chip) to load analysis.
4. Try typing guided analytics commands into the **Ask** bar:
   * **Data Credibility**: Type `"can I trust this data"` or click the chip. The screen scrolls to and highlights the **Quality Gate** card.
   * **Planning aids**: Type `"show forecast"`. The screen highlights the **Trends and Forecasts** card.
   * **Visual Evidence**: Type `"show charts"`. The screen highlights the **Visual Analytics** card. Use the live search field to look for "region", and click filter buttons to cycle categories.
   * **Business Decisions**: Type `"what should we do"`. The screen highlights the **Recommendations & Action Center** card.
   * **Report Export**: Type `"download pdf"`. The browser compiles and starts downloading the PDF executive report.
   * **Compliance Audit**: Type `"show technical evidence"`. The screen highlights the **Technical Evidence Drawer**.
   * **Help fallback**: Type an arbitrary phrase (e.g. `"test"`) to view the inline command guide list.
5. In Visual Analytics, toggle a chart card to its table format (e.g., Regional Revenue Share table) and expand the interpretation details.
6. Verify the diagnostics shape check logs are clean in the Technical Evidence Drawer.
7. Upload `data/sample/sales_sample.csv` and verify the status indicators transition from *"Uploading file"* to *"Ready (upload mode)"*.
8. Export report outputs to verify that blocked states prevent report compilation.

## 5. Artifact And Operations Talking Points

- Markdown and PDF reports can be generated from `AnalysisResponse`.
- Report export endpoints can download generated Markdown and PDF reports.
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
