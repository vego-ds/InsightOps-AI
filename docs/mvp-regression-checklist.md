# MVP Regression Checklist

Use this checklist before recording a demo, sharing the local MVP, or starting a larger change. The goal is to prove the local FastAPI + Next.js workspace still works end to end.

## 1. Backend Checks

From the repository root:

```bash
source venv/bin/activate
ruff check .
python3 -m pytest
```

Expected result:

- Ruff exits cleanly.
- Pytest exits cleanly.
- No generated cache files are staged.
- No files under `scratch/datasets` are staged.

Quick API check:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
curl http://127.0.0.1:8000/health
```

Expected response includes:

```json
{"status":"ok","service":"insightops-ai"}
```

## 2. Frontend Checks

From `web/`:

```bash
npm run lint
npx tsc --noEmit
```

Expected result:

- ESLint exits cleanly.
- TypeScript exits cleanly.
- No `.next` or `node_modules` files are staged.

## 3. Browser Smoke Test

Start both services:

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

```bash
cd web
npm run dev
```

Open:

```text
http://localhost:3000
```

Verify:

- Page is not blank.
- Header shows `InsightOps-AI`.
- No framework error overlay appears.
- No relevant console errors appear.
- Preview tab is visible.
- Schema and Artifacts tabs are disabled before upload.
- Chat input is disabled before upload.
- Run History shows an empty state.
- Mobile width does not create horizontal page overflow.

## 4. Happy Path Smoke Flow

1. Upload `data/sample/sales_sample.csv`.
2. Confirm Preview shows rows and columns.
3. Open Schema.
4. Confirm column list and selected column detail render.
5. Ask: `Summarize this dataset`
6. Confirm an assistant message appears with an execution timeline.
7. Confirm notebook cell, stdout/stderr area, and final message render.
8. Confirm Artifacts tab becomes enabled.
9. Confirm a table, chart, or markdown artifact renders safely.
10. Ask: `Show revenue by region`
11. Ask follow-up: `Now by product`
12. Confirm run history contains each run.
13. Click a prior run in history.
14. Confirm artifact focus and timeline are restored for that run.
15. Export an artifact.
16. Export the run report.
17. Click Clear dataset.
18. Confirm dataset, chat, artifacts, run history, execution timeline, notebook state, and canvas mode reset.

## 5. Runtime Mode Checks

Run each mode with the backend and repeat the happy path upload/chat smoke flow.

### Mock

```bash
INSIGHTOPS_RUNTIME=mock uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Expected:

- Deterministic notebook stream appears.
- Prompt containing `error` or `fail` emits mock failure and repair events.
- Artifacts render.

### Local Python

```bash
INSIGHTOPS_RUNTIME=local_python uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Expected:

- Controlled Python template runs against the registered dataset path.
- Stdout appears.
- Real artifacts are emitted from the uploaded CSV.
- No user-provided code is executed.

### Docker

```bash
INSIGHTOPS_RUNTIME=docker uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Expected:

- Docker availability is checked.
- If Docker is available, the deterministic template runs in a constrained container.
- If Docker is unavailable, the stream emits a controlled runtime error.
- Dataset mount remains read-only and inside the storage root.

## 6. Failure-Mode Tests

### Backend Offline

1. Stop the backend.
2. Keep the frontend running.
3. Try to upload a CSV.

Expected:

- Upload shows a readable backend-offline message.
- No dataset is stored in frontend state.

### Docker Unavailable

1. Start backend with `INSIGHTOPS_RUNTIME=docker`.
2. Ensure Docker is stopped or unavailable.
3. Upload a CSV and ask: `Summarize this dataset`

Expected:

- Stream returns a controlled runtime error.
- UI renders an error message without crashing.

### Upload Failure

1. Upload a non-CSV file.

Expected:

- Backend returns the unsupported file contract.
- UI shows a readable upload failure.
- Chat and Schema remain disabled.

### Runtime Error Prompt

In mock runtime, ask:

```text
Force an error in the notebook
```

Expected:

- Failed cell renders.
- Traceback is inside collapsible technical details.
- Repair/self-healing panel renders.
- Final assistant message indicates recovery.

## 7. Dataset Cleanup Verification

1. Start backend and frontend.
2. Upload `data/sample/sales_sample.csv`.
3. Confirm a new CSV appears under `scratch/datasets`.
4. Click Clear dataset in the workspace.
5. Confirm the stored file is removed from `scratch/datasets`.
6. Confirm the UI returns to the no-dataset state.
7. Confirm no stale chat messages, artifacts, run history, active run id, selected artifact id, selected column, execution events, or notebook cells remain.

Do not commit `scratch/datasets`.
