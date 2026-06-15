# Regression Verification Checklist

## Scope

This checklist verifies the local FastAPI and Next.js workspace before merging runtime, planner, upload, artifact, or frontend state-management changes.

## Backend Verification

| Check | Command or Action | Expected Result |
| --- | --- | --- |
| Dependency verification | `python3 scripts/verify_dependencies.py` | Pass |
| Lint | `ruff check .` | Pass |
| Test suite | `python3 -m pytest` | Pass |
| Health route | `curl http://127.0.0.1:8000/health` | `{"status":"ok","service":"insightops-ai"}` |
| OpenAPI | Open `/docs` | Schema renders |

## Frontend Verification

| Check | Command | Expected Result |
| --- | --- | --- |
| Lint | `cd web && npm run lint` | Pass |
| Type check | `cd web && npx tsc --noEmit` | Pass |
| Development server | `cd web && npm run dev` | Workspace available on port `3000` |

## Browser Smoke Test

| Step | Expected Result |
| --- | --- |
| Upload `data/sample/sales_sample.csv` | Dataset summary and preview render |
| Open Schema tab | Column list and detail card render |
| Send `Summarize this dataset` | Streaming timeline appears |
| Send `Show revenue by region` | Grouped artifacts appear |
| Send `Now by product` | Follow-up context updates grouping |
| Select a previous run | Artifact and timeline context restore |
| Export artifact | CSV or Markdown download is produced |
| Export run report | Markdown report download is produced |
| Clear dataset | Dataset file is deleted and UI state resets |

## Runtime Mode Matrix

| Mode | Command | Required Checks |
| --- | --- | --- |
| `mock` | `INSIGHTOPS_RUNTIME=mock uvicorn app.main:app --host 0.0.0.0 --port 8000` | Deterministic stream, repair prompt behavior, artifact rendering |
| `local_python` | `INSIGHTOPS_RUNTIME=local_python uvicorn app.main:app --host 0.0.0.0 --port 8000` | Controlled template execution, stdout capture, real artifacts |
| `docker` | `INSIGHTOPS_RUNTIME=docker uvicorn app.main:app --host 0.0.0.0 --port 8000` | Docker availability handling, constrained execution, controlled unavailable-runtime error |

## Failure-Mode Matrix

| Scenario | Procedure | Expected Result |
| --- | --- | --- |
| Backend offline | Stop backend and upload CSV from frontend | Controlled upload-service error |
| Docker unavailable | Start backend with `INSIGHTOPS_RUNTIME=docker` while Docker is stopped | Controlled runtime error event |
| Unsupported upload | Upload a non-CSV file | Unsupported file response; dataset state remains empty |
| Runtime failure prompt | In mock runtime, send `Force an error in the notebook` | Failed cell, repair events, final message |
| Dataset cleanup | Upload CSV, clear dataset, inspect `scratch/datasets` | Stored file removed and frontend state reset |

## State Reset Requirements

After dataset cleanup, these stores must not retain run-scoped state:

| State Area | Required State |
| --- | --- |
| Dataset | No active dataset |
| Chat | No messages |
| Artifacts | No selected artifact or active run |
| Run history | No run records |
| Execution | No run events |
| Notebook | No cells or repair state |
| Canvas | Preview mode |
