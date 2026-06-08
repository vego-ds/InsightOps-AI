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

Uploads are CSV-only with a default maximum size of 100 MB (104,857,600 bytes). This limit can be customized at runtime using the `INSIGHTOPS_MAX_UPLOAD_BYTES` environment variable.

To support large uploads safely without exhausting server memory, files are streamed in 64 KB chunks directly to a temporary file. The size limit is enforced dynamically during streaming, raising a `413 Payload Too Large` error if the limit is exceeded. Temporary files are guaranteed to be unlinked (deleted) immediately upon request completion or on any error.

### Reverse Proxy Configuration
If deploying behind a reverse proxy (e.g., Nginx, Apache) or an API Gateway, ensure the server configuration permits large request bodies. For example, in Nginx, add or update the following directive:

```nginx
client_max_body_size 100M;
```

Otherwise, the proxy may reject the upload before it reaches the FastAPI application.

Report export endpoints generate Markdown and PDF artifacts in temporary per-request directories. No persistent report storage is configured, and uploaded files are removed after request processing. Deployment platforms should treat report outputs as response artifacts rather than stored application data. Upload limits still apply to report generation from uploaded CSV files.

The static dashboard is served from `GET /`.

OpenRouter is optional for narrative writing. Configure credentials as platform secrets, not committed files. The default narrative provider remains disabled.

## Hosted Platforms

For Render, Fly.io, Railway, or similar platforms:

- Build command: `python3 -m pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`
