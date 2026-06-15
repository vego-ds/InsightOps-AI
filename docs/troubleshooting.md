# Troubleshooting

This guide covers common local operational issues for InsightOps-AI.

## Frontend And Backend Ports

The frontend and backend are separate services:

- Frontend Next.js workspace: `http://localhost:3000`
- Backend FastAPI API: `http://127.0.0.1:8000`
- Backend static dashboard shell: `http://127.0.0.1:8000`

The frontend proxies `/api/*` requests to the backend. If the backend is offline, the frontend can load but upload and analysis calls will fail.

## Port 8000 Is Already In Use

Check what is using port 8000:

```bash
lsof -i :8000
```

Stop the process:

```bash
kill <PID>
```

Then restart the backend:

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Port 3000 Is Already In Use

Check what is using port 3000:

```bash
lsof -i :3000
```

Stop the process:

```bash
kill <PID>
```

Then restart the frontend:

```bash
cd web
npm run dev
```

If Next.js chooses another port, free port 3000 to preserve the standard local route.

## Backend Offline During Upload

Symptom:

- The frontend loads.
- Upload shows a backend-offline or upload-service error.

Check:

```bash
curl http://127.0.0.1:8000/health
```

If the request fails, start the backend:

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then retry the upload from `http://localhost:3000`.

## Upload Failure

Common causes:

- File is not a CSV.
- Backend is offline.
- CSV cannot be parsed into the preview contract.
- File exceeds the configured upload limit.

Use the bundled sample for a known-good smoke test:

```text
data/sample/sales_sample.csv
```

## Docker Runtime Timeout Or Cold Image Start

The Docker runtime uses `python:3.12-slim`. The first run may be slow if the image is not present locally.

Warm Docker before runtime verification:

```bash
docker pull python:3.12-slim
docker run --rm python:3.12-slim python --version
```

Then start the backend:

```bash
INSIGHTOPS_RUNTIME=docker uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If Docker is unavailable, the runtime should emit a controlled runtime error instead of crashing the frontend.

## Docker Runtime Is Unavailable

Check Docker:

```bash
docker version
```

If Docker Desktop is installed, make sure it is running. If Docker is intentionally unavailable, use:

```bash
INSIGHTOPS_RUNTIME=mock uvicorn app.main:app --host 0.0.0.0 --port 8000
```

or:

```bash
INSIGHTOPS_RUNTIME=local_python uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Dataset Cleanup

Uploaded datasets are stored as local files under:

```text
scratch/datasets
```

Use the Clear dataset button in the frontend to delete the registered dataset and reset the workspace state.

If local testing leaves files behind, confirm the backend is running and use Clear dataset from the UI. Do not commit files from `scratch/datasets`.

## Do Not Commit Local Runtime Files

Do not commit:

- `scratch/datasets`
- `web/.next`
- `web/node_modules`
- `venv`
- `.venv`
- `__pycache__`
- `*.pyc`
- `.pytest_cache`
- `.ruff_cache`
- `.env`

These are local runtime, cache, dependency, or secret-bearing paths.

## Known Limitations

- Local workspace only.
- No user auth.
- No persistent database.
- No multi-user workspace isolation.
- No production runtime worker pool.
- LLM-backed planning is optional and must retain deterministic fallback behavior.
- Uploaded datasets are local files.
- Docker runtime is a local prototype.
