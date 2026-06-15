# Workflow Runbook

## Objective

Validate the end-to-end workspace flow in a controlled local environment: upload, preview, schema inspection, streaming analysis, notebook events, artifacts, run history, exports, and dataset cleanup.

## Prerequisites

| Requirement | Value |
| --- | --- |
| Backend URL | `http://127.0.0.1:8000` |
| Frontend URL | `http://localhost:3000` |
| Sample file | `data/sample/sales_sample.csv` |
| Recommended runtime | `local_python` |

## Startup Commands

Backend:

```bash
source venv/bin/activate
INSIGHTOPS_RUNTIME=local_python uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd web
npm run dev
```

## Execution Sequence

| Step | Action | Expected Result |
| --- | --- | --- |
| 1 | Open `http://localhost:3000` | Workspace renders with no active dataset |
| 2 | Upload `data/sample/sales_sample.csv` | Dataset preview contract is rendered |
| 3 | Open Preview tab | Row count, column count, and preview rows are visible |
| 4 | Open Schema tab | Column keys, labels, data types, nullability, and samples are visible |
| 5 | Send `Summarize this dataset` | A streaming run is created and notebook events render |
| 6 | Send `Show revenue by region` | Grouped metric artifacts are generated |
| 7 | Send `Now by product` | Follow-up context reuses the metric and changes grouping |
| 8 | Open Artifacts tab | Chart, table, and markdown artifacts render safely |
| 9 | Select a previous run | Run history restores run-scoped artifacts and timeline context |
| 10 | Export artifact and run report | Browser downloads CSV or Markdown outputs |
| 11 | Clear dataset | Backend deletes registered file and frontend stores reset |

## Verification Points

| Surface | Verification |
| --- | --- |
| Upload | Unsupported files are rejected; CSV preview uses `insightops.file-preview.v1` |
| Planner | Explicit prompts map to deterministic or hybrid-resolved intents |
| Runtime | Notebook status, cell, stdout, stderr, failure, repair, artifact, and final events render |
| Canvas | Artifacts tab focuses generated outputs without layout expansion |
| History | Prior run selection restores artifact focus |
| Cleanup | Active dataset, selected column, chat, artifacts, run history, execution events, notebook cells, and canvas mode reset |

## Completion Criteria

The runbook is complete when the workspace returns to the no-dataset state and `scratch/datasets` no longer contains the uploaded dataset file.
