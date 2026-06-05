import os

from pydantic import BaseModel


class AppSettings(BaseModel):
    app_name: str = "InsightOps-AI"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    max_upload_bytes: int = 1_000_000
    narrative_provider: str = "disabled"


def load_app_settings() -> AppSettings:
    return AppSettings(
        environment=os.getenv("INSIGHTOPS_ENVIRONMENT", "development"),
        host=os.getenv("INSIGHTOPS_HOST", "0.0.0.0"),
        port=_get_int_env("INSIGHTOPS_PORT", 8000),
        max_upload_bytes=_get_int_env(
            "INSIGHTOPS_MAX_UPLOAD_BYTES",
            1_000_000,
        ),
        narrative_provider=os.getenv(
            "INSIGHTOPS_NARRATIVE_PROVIDER",
            "disabled",
        ),
    )


def _get_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return int(raw_value)
