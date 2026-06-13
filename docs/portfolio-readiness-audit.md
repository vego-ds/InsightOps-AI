# Portfolio Readiness Audit

Date: 2026-06-14

## Scope Checked

This audit reviewed the local MVP repository for portfolio readiness across:

- Next.js frontend structure under `web/src`.
- Zustand stores for dataset, chat, artifact, run history, canvas, execution, and notebook state.
- FastAPI backend routes and API contracts.
- Runtime adapter structure for `mock`, `local_python`, and `docker`.
- Dataset registry, storage, deletion, and cleanup safety.
- Tests and validation commands.
- Documentation accuracy and demo readiness.
- Git ignore rules and generated-file hygiene.
- User-facing copy in the current workspace and legacy static dashboard.

## What Was Cleaned Or Updated

- Updated root `.gitignore` to explicitly cover coverage output and frontend generated/dependency paths:
  - `coverage/`
  - `htmlcov/`
  - `.coverage`
  - `web/.next/`
  - `web/node_modules/`
  - `web/out/`
  - `web/coverage/`
  - `web/*.tsbuildinfo`
- Refreshed `README.md` to explicitly describe:
  - Next.js frontend.
  - Zustand state architecture.
  - FastAPI backend.
  - Runtime adapter boundary.
  - Artifact pipeline.
  - Dataset registry.
  - Local MVP limitations.
- Replaced stale legacy-dashboard-oriented demo material with the current MVP demo script.
- Added a regression checklist for backend, frontend, browser, runtime modes, failure modes, and dataset cleanup.
- Added troubleshooting coverage for port conflicts, backend offline upload errors, Docker warmup, Docker timeout behavior, and local files not to commit.
- Removed stale `Sentryx` console wording from the legacy static dashboard script.
- Removed a successful binding-check `console.log` from the legacy static dashboard script.
- Reworded a legacy dashboard render-error message so users are not told to inspect the browser console as primary guidance.
- Added a minimum size guard to the Recharts `ResponsiveContainer` to prevent zero/negative dimension warnings during artifact rendering.

## Architectural Or Structural Changes

No major architecture changes were made.

Small structural/hygiene changes:

- Root ignore rules were expanded.
  - Why: make repository hygiene obvious from the root, even though the frontend also has its own `.gitignore`.
  - Problem solved: prevents accidental staging of generated frontend output, coverage artifacts, and local dependency folders.
  - Safety: ignore-only change; no runtime behavior affected.
- Chart container minimum dimensions were added.
  - Why: previous dev logs showed Recharts width/height warnings during artifact rendering.
  - Problem solved: reduces console noise and improves demo polish.
  - Safety: preserves the existing chart contract and renderer; only adds minimum dimensions to the existing responsive container.

## Documentation Updates

Updated or created:

- `README.md`
- `docs/demo-script.md`
- `docs/mvp-regression-checklist.md`
- `docs/troubleshooting.md`
- `docs/portfolio-readiness-audit.md`

No `docs/known-limitations.md` was created because limitations are already covered in `README.md` and `docs/troubleshooting.md`.

## Frontend Audit Notes

- Frontend files are organized by surface:
  - `components/artifacts`
  - `components/chat`
  - `components/datasets`
  - `components/execution`
  - `components/history`
  - `components/notebook`
  - `components/workspace`
  - `stores`
  - `types`
  - `lib`
- Zustand stores remain purposeful and scoped:
  - `dataset-store`: active dataset, upload state, selected column.
  - `chat-store`: messages and assistant status.
  - `artifact-store`: artifact collection, active run, selected artifact.
  - `run-history-store`: in-memory run records and selected run.
  - `canvas-store`: active canvas mode and user focus lock.
  - `execution-store`: execution event history.
  - `notebook-store`: notebook cell and repair state.
- Search confirmed no inline `?? []` or `?? {}` remains under `web/src`.
- ESLint and TypeScript pass.
- Browser smoke confirmed the no-dataset state renders and mobile width `390px` has no horizontal overflow.

## Backend Audit Notes

- API contracts remain stable for:
  - dataset upload
  - dataset delete
  - analysis request
  - analysis runs
  - SSE run events
  - artifact events
- Runtime architecture remains clear:
  - `RuntimeAdapter` protocol.
  - `MockRuntimeAdapter`.
  - `LocalPythonRuntimeAdapter`.
  - `DockerRuntimeAdapter`.
- Dataset lifecycle safety remains covered:
  - dataset paths resolve through registry metadata
  - file deletion validates path containment
  - cleanup utility is tested
  - uploaded datasets are stored under `scratch/datasets`
- Ruff and pytest pass.

## Git And File Hygiene

Tracked generated-file check found no tracked matches for:

- `__pycache__`
- `.pyc`
- `.pytest_cache`
- `.ruff_cache`
- `scratch/datasets`
- `web/.next`
- `web/node_modules`
- `venv`
- coverage output
- `.env`

Ignored local directories may exist during development, including `web/node_modules`, `web/.next`, `venv`, `.pytest_cache`, `.ruff_cache`, and Python `__pycache__` directories. They are not part of the source artifact.

## Manual QA Results

Browser smoke:

- Opened frontend at `http://localhost:3000`.
- Confirmed page title: `InsightOps-AI`.
- Confirmed no-dataset workspace rendered.
- Confirmed upload area rendered.
- Confirmed empty run history rendered.
- Confirmed mobile viewport width `390px` had no horizontal overflow.

API-assisted MVP smoke:

- Uploaded `data/sample/sales_sample.csv` through `POST /api/datasets/upload`.
- Confirmed `200` upload response.
- Confirmed dataset preview had `200` rows and `10` columns.
- Created analysis run through `POST /api/analysis/runs`.
- Confirmed run status `created`.
- Read SSE stream and confirmed `run.artifact` and `run.final` events.
- Deleted dataset through `DELETE /api/datasets/{datasetId}`.
- Confirmed delete status `deleted`.

Manual browser automation limitation:

- The in-app browser automation surface detected the file input but did not expose file attachment automation for this environment.
- Full UI upload/export click-through was therefore not fully automated in-browser during this audit.
- The equivalent backend upload, streaming run, artifact/final event, and dataset cleanup path was verified through the local API.

## Validation Results

Backend:

```text
node --check app/static/app.js: passed
ruff check .: passed
python3 -m pytest: 342 passed
```

Frontend:

```text
cd web && npm run lint: passed
cd web && npx tsc --noEmit: passed
```

Repository hygiene:

```text
No tracked generated/cache/dependency artifacts found.
No inline ?? [] or ?? {} fallbacks found under web/src.
```

## Remaining Known Limitations

- Local MVP only.
- No user auth.
- No persistent database.
- No multi-user workspace isolation.
- No production runtime worker pool.
- No hosted deployment yet.
- No LLM planning integration yet.
- Uploaded datasets are local files under `scratch/datasets`.
- Docker runtime is a local prototype.
- Run history and artifact history are in-memory frontend state.

## Final Portfolio Readiness Status

Status: portfolio-ready local MVP.

The repository now presents the MVP accurately and professionally: deterministic data upload, schema inspection, chat-driven runs, notebook-style execution, artifacts, exports, run history, and dataset cleanup are documented with clear setup, demo, regression, troubleshooting, and audit materials. The project should be reviewed as a strong local MVP and engineering portfolio artifact, not as a production SaaS deployment.
