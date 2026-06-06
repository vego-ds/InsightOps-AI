from insightops.narrative.factory import get_narrative_provider
from insightops.narrative.openrouter_provider import OpenRouterNarrativeProvider
from insightops.narrative.providers import DisabledNarrativeProvider


def test_factory_returns_openrouter_provider() -> None:
    provider = get_narrative_provider("openrouter")

    assert isinstance(provider, OpenRouterNarrativeProvider)


def test_default_provider_remains_disabled(monkeypatch) -> None:
    monkeypatch.delenv("INSIGHTOPS_NARRATIVE_PROVIDER", raising=False)

    provider = get_narrative_provider()

    assert isinstance(provider, DisabledNarrativeProvider)


def test_unknown_provider_falls_back_to_disabled() -> None:
    provider = get_narrative_provider("unknown")

    assert isinstance(provider, DisabledNarrativeProvider)
