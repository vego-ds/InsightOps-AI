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
3. Explain source metadata: source type, file name, file size, collection method, and raw record count.
4. Explain validation results: total, valid, invalid rows, and row-level errors.
5. Explain data profile: date range, unique entities, duplicate order IDs, missing fields, and numeric summaries.
6. Explain quality score: deterministic 0-100 score, grade, issues, and recommendations.
7. Explain the quality gate: pass, warning, or blocked status; confidence level; allowed outputs; and LLM narrative eligibility.
8. Explain how missing data, duplicates, invalid rows, and security flags lower confidence or require human review.
9. Explain preparation: cleaned text and derived analytical fields such as net revenue, quarters, discount flags, and reconciliation differences.
10. Explain transformation lineage: each deterministic preparation step records affected records and created or modified fields.
11. Explain manipulation summaries: monthly revenue, ranked regions/products/sales reps, and discount behavior by product.
12. Explain trend analysis: monthly revenue, order count, units sold, average order value, average discount, direction, and warnings.
13. Explain forecast readiness: ready, limited, or not ready, with confidence and limitations.
14. Explain baseline forecasts: last-period, moving average, and simple trend projection are deterministic planning aids, not ML predictions.
15. Explain KPI results: revenue, order count, units sold, average order value.
16. Explain security guardrails: prompt-injection detection and human-review flags.
17. Explain anomaly detection: fixed business rules still catch high revenue, high quantity, high discount, and zero revenue.
18. Explain IQR statistical outliers: thresholds are calculated from the data, are auditable, and flag unusual values without automatically removing them.
19. Explain product-relative outliers: revenue can be unusual within a product segment even when it is not globally unusual.
20. Explain visual analytics: each chart answers a business question, includes a deterministic interpretation, links to insight IDs, and carries recommended actions.
21. Explain trend and forecast charts: monthly movement and next-period baselines support planning workflows without external forecasting libraries.
22. Explain Pareto revenue concentration: show whether product revenue is concentrated in a few products.
23. Explain discount concentration and data quality charts: show discount reliance and whether the dataset is reliable enough for executive reporting.
24. Explain how visual evidence supports stakeholder recommendations.
25. Explain business recommendations: each has evidence, owner role, expected impact, and a follow-up metric.
26. Explain workflow improvements: recommendations become operational process changes.
27. Explain executive insights and recommended actions.
28. Upload `data/sample/sales_sample.csv` and show the same response contract.

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
