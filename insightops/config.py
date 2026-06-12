import os

from pydantic import BaseModel


class AppSettings(BaseModel):
    app_name: str = "InsightOps-AI"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    max_upload_bytes: int = 104_857_600
    narrative_provider: str = "disabled"
    openrouter_api_key: str | None = None
    openrouter_model: str = "openrouter/auto"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    runtime: str = "mock"


def load_app_settings() -> AppSettings:
    return AppSettings(
        environment=os.getenv("INSIGHTOPS_ENVIRONMENT", "development"),
        host=os.getenv("INSIGHTOPS_HOST", "0.0.0.0"),
        port=_get_int_env("INSIGHTOPS_PORT", 8000),
        max_upload_bytes=_get_int_env(
            "INSIGHTOPS_MAX_UPLOAD_BYTES",
            104_857_600,
        ),
        narrative_provider=os.getenv(
            "INSIGHTOPS_NARRATIVE_PROVIDER",
            "disabled",
        ),
        openrouter_api_key=os.getenv("INSIGHTOPS_OPENROUTER_API_KEY"),
        openrouter_model=os.getenv(
            "INSIGHTOPS_OPENROUTER_MODEL",
            "openrouter/auto",
        ),
        openrouter_base_url=os.getenv(
            "INSIGHTOPS_OPENROUTER_BASE_URL",
            "https://openrouter.ai/api/v1",
        ),
        runtime=os.getenv("INSIGHTOPS_RUNTIME", "mock"),
    )


def _get_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return int(raw_value)
