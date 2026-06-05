# InsightOps-AI Agent Instructions

## Project goal

InsightOps-AI is a production-style AI-powered sales analytics automation platform.

It should ingest sales data, validate schemas, compute sales KPIs, detect anomalies, generate charts, and produce executive-ready insights with auditability.

## Engineering rules

- Keep changes small and reviewable.
- Prefer deterministic business logic before adding LLM behavior.
- Add tests for every new module.
- Do not commit secrets, API keys, tokens, or credentials.
- Use typed Python.
- Use Pydantic models for input and output contracts.
- Keep AI generation behind clear interfaces.
- Preserve auditability for data transformations and insight generation.
- Do not commit generated cache files such as `__pycache__`, `.pyc`, `.pytest_cache`, or `.ruff_cache`.
- Keep `app/main.py` thin when possible; move orchestration into domain or pipeline modules.

## Commands

```bash
ruff format . # Run code formatting (restructure style and spacing)
ruff check . # Run code linting (find code quality bugs and dead code)
python3 -m pytest # Run automated tests
uvicorn app.main:app --host 0.0.0.0 --port 8000 # Run the local development API

```

Initial Project Structure

Use this structure:

app/
  main.py

insightops/
  ingestion/
  validation/
  metrics/
  anomalies/
  insights/
  charts/
  security/
  pipeline/
  audit/

tests/
data/
  sample/
docs/
Done Means Done

A task is complete only when:

The code is simple.
Tests pass.
Ruff passes.
Changed files are summarized.
The work can be explained in an interview.
