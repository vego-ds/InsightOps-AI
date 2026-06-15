# InsightOps-AI

InsightOps-AI is a governed data-analysis workspace for CSV-based sales analytics. The system combines a Next.js workspace, typed FastAPI APIs, a dataset registry, streaming execution events, notebook-style runtime details, artifact rendering, export utilities, and deterministic cleanup controls.

## System Capabilities

| Area | Capability |
| --- | --- |
| Dataset ingestion | CSV upload, preview generation, schema typing, local registry storage, safe deletion |
| Workspace UI | Chat panel, data canvas, schema inspector, artifact gallery, run history |
| Analysis routing | Deterministic intent routing with optional OpenRouter-backed hybrid planning |
| Execution stream | Server-Sent Events for status, notebook cells, stdout, stderr, failures, repair states, artifacts, final answers |
| Runtime modes | Mock simulator, local Python deterministic template, Docker deterministic template |
| Artifacts | Table, chart, and markdown artifacts with frontend-only export support |
| Governance | Quality gates, prompt-injection checks, deterministic fallback behavior, audit events |

## Architecture

```text
Next.js workspace
  -> Zustand workspace stores
  -> FastAPI dataset and analysis APIs
  -> dataset registry and scratch storage
  -> conversation context store
  -> hybrid planner
  -> runtime adapter boundary
  -> execution events and artifacts
  -> frontend rendering, history, and exports
```

## Local URLs

| Surface | URL |
| --- | --- |
| Frontend workspace | `http://localhost:3000` |
| Backend API | `http://127.0.0.1:8000` |
| OpenAPI schema | `http://127.0.0.1:8000/openapi.json` |
| API docs | `http://127.0.0.1:8000/docs` |
| Static dashboard shell | `http://127.0.0.1:8000` |

## Local Setup

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
python3 scripts/verify_dependencies.py
```

```bash
cd web
npm install
cd ..
```

Create local environment configuration when OpenRouter-backed behavior is required:

```bash
cp .env.example .env
```

## Runtime Modes

| Mode | Command | Execution Boundary |
| --- | --- | --- |
| `mock` | `INSIGHTOPS_RUNTIME=mock uvicorn app.main:app --host 0.0.0.0 --port 8000` | Deterministic simulator, no Python execution |
| `local_python` | `INSIGHTOPS_RUNTIME=local_python uvicorn app.main:app --host 0.0.0.0 --port 8000` | Controlled deterministic Python template against the registered dataset path |
| `docker` | `INSIGHTOPS_RUNTIME=docker uvicorn app.main:app --host 0.0.0.0 --port 8000` | Controlled deterministic Python template inside a constrained Docker container |

Docker image warm-up:

```bash
docker pull python:3.12-slim
docker run --rm python:3.12-slim python --version
```

## Run Services

Backend:

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd web
npm run dev
```

## Validation

| Layer | Commands |
| --- | --- |
| Backend | `ruff check .` |
| Backend tests | `python3 -m pytest` |
| Dependencies | `python3 scripts/verify_dependencies.py` |
| Frontend lint | `cd web && npm run lint` |
| Frontend types | `cd web && npx tsc --noEmit` |

## Active API Surface

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Static dashboard shell |
| `GET` | `/health` | Service health |
| `POST` | `/api/datasets/upload` | CSV upload and preview contract |
| `DELETE` | `/api/datasets/{dataset_id}` | Dataset registry and file cleanup |
| `POST` | `/api/analysis/request` | Backward-compatible non-streaming analysis request |
| `POST` | `/api/analysis/runs` | Streaming analysis run creation |
| `GET` | `/api/analysis/runs/{run_id}/events` | Server-Sent Events stream |
| `GET` | `/analysis/sample` | Deterministic sample sales analysis |
| `POST` | `/analysis/upload` | Deterministic uploaded sales analysis |
| `POST` | `/analysis/upload/preview` | CSV schema compatibility preview |
| `POST` | `/analysis/upload/report` | Report export for uploaded CSV |
| `POST` | `/analysis/sample/report` | Report export for bundled sample data |

## Smoke Flow

1. Start backend and frontend.
2. Upload `data/sample/sales_sample.csv`.
3. Inspect Preview and Schema tabs.
4. Send `Summarize this dataset`.
5. Send `Show revenue by region`.
6. Send `Now by product`.
7. Review execution timeline and artifacts.
8. Export an artifact and run report.
9. Clear the dataset and confirm workspace state resets.

## Operational Limits

| Limitation | Current State |
| --- | --- |
| Authentication | Not implemented |
| Database persistence | Not implemented |
| Multi-user isolation | Not implemented |
| Production worker pool | Not implemented |
| Dataset storage | Local files under `scratch/datasets` |
| Docker runtime | Local prototype |
| LLM usage | Optional OpenRouter-backed planning and narrative support with deterministic fallback |

## Documentation

| Document | Purpose |
| --- | --- |
| [Application overview](docs/application-overview.md) | Product and capability specification |
| [System design](docs/system-design.md) | Architecture and module boundaries |
| [Deployment](docs/deployment.md) | Runtime, environment, and deployment configuration |
| [Regression checklist](docs/mvp-regression-checklist.md) | Verification checklist |
| [Workflow runbook](docs/workflow-runbook.md) | Operator procedure for presenting the workflow |
| [Troubleshooting](docs/troubleshooting.md) | Local operational issue resolution |
| [Threat model](docs/threat-model.md) | Security boundaries, threats, and mitigations |
