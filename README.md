# InsightOps-AI

InsightOps-AI is a local MVP for an AI-style data analysis workspace. It combines a chat panel, notebook-style execution timeline, and data canvas so a user can upload a CSV, inspect the schema, ask analysis questions, watch deterministic streaming execution events, review generated artifacts, export results, revisit run history, and clean up uploaded datasets.

The current MVP is intentionally deterministic. It does not call an LLM, does not persist data to a database, and does not provide production auth or job queues.

## What It Does

- CSV upload and preview through `POST /api/datasets/upload`.
- Typed schema preview with column details and sample values.
- Chat-driven analysis requests.
- Server-Sent Events streaming execution timeline.
- Notebook-style code cells with stdout, stderr, failures, and repair states.
- Table, chart, and markdown artifacts.
- Artifact export to CSV or Markdown.
- Run report export to Markdown.
- In-memory run history for prompts, final answers, timelines, and artifacts.
- Dataset deletion and cleanup so files in `scratch/datasets` do not accumulate.
- Runtime modes for mock, local Python, and Docker-backed deterministic execution.
- Zustand stores for dataset, chat, canvas, execution, notebook, artifact, and run-history state.

## Architecture

```text
Next.js frontend
  -> Zustand state stores for workspace UI state
  -> FastAPI upload, run creation, SSE event stream, dataset delete APIs
  -> dataset registry and local scratch storage
  -> runtime adapter boundary
  -> deterministic notebook events and artifact pipeline
  -> chat, notebook timeline, artifact gallery, run history, exports
```

Important local surfaces:

- Frontend workspace: `http://localhost:3000`
- Backend API and OpenAPI docs: `http://127.0.0.1:8000`
- Backend legacy static dashboard, if opened directly: `http://127.0.0.1:8000`

## Local Setup

Create and activate a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install backend dependencies:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/verify_dependencies.py
```

Install frontend dependencies:

```bash
cd web
npm install
cd ..
```

Run the backend:

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Run the frontend in a second terminal:

```bash
cd web
npm run dev
```

Open:

```text
http://localhost:3000
```

## Runtime Modes

Runtime mode is selected with `INSIGHTOPS_RUNTIME`.

### Mock

Default mode. Emits deterministic notebook, stdout, artifact, and final events without executing Python.

```bash
INSIGHTOPS_RUNTIME=mock uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Local Python

Runs a controlled deterministic Python template against the registered local dataset path. It does not execute user-provided code.

```bash
INSIGHTOPS_RUNTIME=local_python uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker

Runs the deterministic Python template in a local Docker container with read-only dataset mount, no network, read-only filesystem, and resource limits where available. It is a local prototype, not a production worker pool.

```bash
INSIGHTOPS_RUNTIME=docker uvicorn app.main:app --host 0.0.0.0 --port 8000
```

To warm the Docker image:

```bash
docker pull python:3.12-slim
docker run --rm python:3.12-slim python --version
```

## Validation Commands

Backend:

```bash
source venv/bin/activate
ruff check .
python3 -m pytest
```

Frontend:

```bash
cd web
npm run lint
npx tsc --noEmit
```

## Sample Smoke Flow

1. Start the backend on `http://127.0.0.1:8000`.
2. Start the frontend on `http://localhost:3000`.
3. Upload `data/sample/sales_sample.csv`.
4. Review the Preview tab.
5. Open the Schema tab and select a few columns.
6. Ask: `Summarize this dataset`
7. Ask: `Show revenue by region`
8. Ask the follow-up: `Now by product`
9. Watch the streaming execution timeline and notebook cell.
10. Open the Artifacts tab.
11. Export an artifact.
12. Export the run report from Run History.
13. Click Clear dataset and confirm the workspace resets.

## API Endpoints

Current MVP endpoints include:

- `GET /`: legacy static dashboard shell.
- `GET /health`: service health.
- `POST /api/datasets/upload`: CSV upload and preview.
- `DELETE /api/datasets/{dataset_id}`: delete registered dataset and stored file.
- `POST /api/analysis/request`: backward-compatible non-streaming placeholder.
- `POST /api/analysis/runs`: create streaming analysis run.
- `GET /api/analysis/runs/{run_id}/events`: Server-Sent Events stream.
- `GET /docs`: FastAPI OpenAPI documentation.
- `GET /openapi.json`: OpenAPI schema.

The repository also contains older deterministic sales analysis/report endpoints used by backend tests and the legacy dashboard path.

## Known Limitations

- Local MVP only.
- No user auth.
- No persistent database.
- No multi-user workspace isolation.
- No production runtime worker pool.
- No LLM planning integration yet.
- No hosted deployment yet.
- Uploaded datasets are local files in `scratch/datasets`.
- Docker runtime is a local prototype.

## Documentation

- [MVP regression checklist](docs/mvp-regression-checklist.md)
- [Demo script](docs/demo-script.md)
- [Troubleshooting](docs/troubleshooting.md)
- [System design](docs/system-design.md)
- [Application overview](docs/application-overview.md)
- [Threat model](docs/threat-model.md)
- [Deployment guide](docs/deployment.md)
- [Portfolio summary](docs/portfolio-summary.md)
