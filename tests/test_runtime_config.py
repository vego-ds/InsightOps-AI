from insightops.config import load_app_settings


def test_default_max_upload_bytes_is_100_mb(monkeypatch) -> None:
    monkeypatch.delenv("INSIGHTOPS_MAX_UPLOAD_BYTES", raising=False)

    settings = load_app_settings()

    assert settings.max_upload_bytes == 104_857_600


def test_environment_override_for_max_upload_bytes(monkeypatch) -> None:
    monkeypatch.setenv("INSIGHTOPS_MAX_UPLOAD_BYTES", "250")

    settings = load_app_settings()

    assert settings.max_upload_bytes == 250


def test_default_narrative_provider_is_disabled(monkeypatch) -> None:
    monkeypatch.delenv("INSIGHTOPS_NARRATIVE_PROVIDER", raising=False)

    settings = load_app_settings()

    assert settings.narrative_provider == "disabled"


def test_openrouter_defaults_do_not_require_environment(monkeypatch) -> None:
    monkeypatch.delenv("INSIGHTOPS_OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("INSIGHTOPS_OPENROUTER_MODEL", raising=False)
    monkeypatch.delenv("INSIGHTOPS_OPENROUTER_BASE_URL", raising=False)

    settings = load_app_settings()

    assert settings.openrouter_api_key is None
    assert settings.openrouter_model == "openrouter/auto"
    assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"


def test_default_port_is_8000(monkeypatch) -> None:
    monkeypatch.delenv("INSIGHTOPS_PORT", raising=False)

    settings = load_app_settings()

    assert settings.port == 8000
