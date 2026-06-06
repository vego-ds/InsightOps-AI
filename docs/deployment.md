# Deployment

InsightOps-AI targets Python 3.12.

## Local Verification

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Verify dependencies:

```bash
python3 scripts/verify_dependencies.py
```

Run tests:

```bash
python3 -m pytest
```

Run linting:

```bash
ruff check .
```

Start the API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Health check: `/health`

## Environment Variables

- `INSIGHTOPS_ENVIRONMENT`
- `INSIGHTOPS_HOST`
- `INSIGHTOPS_PORT`
- `INSIGHTOPS_MAX_UPLOAD_BYTES`
- `INSIGHTOPS_NARRATIVE_PROVIDER`
- `INSIGHTOPS_OPENROUTER_API_KEY`
- `INSIGHTOPS_OPENROUTER_MODEL`
- `INSIGHTOPS_OPENROUTER_BASE_URL`

Uploads are CSV-only with a default maximum size of 1 MB.

The static dashboard is served from `GET /`.

OpenRouter is optional for narrative writing. Configure credentials as platform secrets, not committed files. The default narrative provider remains disabled.

## Hosted Platforms

For Render, Fly.io, Railway, or similar platforms:

- Build command: `python3 -m pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`
