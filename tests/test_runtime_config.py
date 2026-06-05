from insightops.config import load_app_settings


def test_default_max_upload_bytes_is_one_mb(monkeypatch) -> None:
    monkeypatch.delenv("INSIGHTOPS_MAX_UPLOAD_BYTES", raising=False)

    settings = load_app_settings()

    assert settings.max_upload_bytes == 1_000_000


def test_environment_override_for_max_upload_bytes(monkeypatch) -> None:
    monkeypatch.setenv("INSIGHTOPS_MAX_UPLOAD_BYTES", "250")

    settings = load_app_settings()

    assert settings.max_upload_bytes == 250


def test_default_narrative_provider_is_disabled(monkeypatch) -> None:
    monkeypatch.delenv("INSIGHTOPS_NARRATIVE_PROVIDER", raising=False)

    settings = load_app_settings()

    assert settings.narrative_provider == "disabled"


def test_default_port_is_8000(monkeypatch) -> None:
    monkeypatch.delenv("INSIGHTOPS_PORT", raising=False)

    settings = load_app_settings()

    assert settings.port == 8000
