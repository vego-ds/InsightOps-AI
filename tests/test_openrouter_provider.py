from insightops.config import AppSettings
from insightops.narrative.openrouter_provider import OpenRouterNarrativeProvider
from insightops.pipeline.sample_analysis import analyze_sample_sales_data


def test_missing_openrouter_api_key_returns_deterministic_fallback() -> None:
    provider = OpenRouterNarrativeProvider(
        AppSettings(openrouter_api_key=None)
    )

    narrative = provider.generate(analyze_sample_sales_data())

    assert narrative.mode == "openrouter_missing_key_fallback"
    assert "Missing OpenRouter API key." in narrative.warnings


def test_openrouter_provider_does_not_throw_when_key_is_missing() -> None:
    provider = OpenRouterNarrativeProvider(
        AppSettings(openrouter_api_key=None)
    )

    narrative = provider.generate(analyze_sample_sales_data())

    assert narrative.narrative


def test_malformed_openrouter_response_falls_back_deterministically() -> None:
    provider = OpenRouterNarrativeProvider(
        AppSettings(openrouter_api_key="test-key")
    )
    provider._post_chat_completion = lambda analysis: {"choices": []}

    narrative = provider.generate(analyze_sample_sales_data())

    assert narrative.mode == "openrouter_fallback"
    assert any(
        "Malformed provider response" in warning
        for warning in narrative.warnings
    )


def test_provider_request_failure_falls_back_deterministically() -> None:
    provider = OpenRouterNarrativeProvider(
        AppSettings(openrouter_api_key="test-key")
    )

    def raise_error(_analysis):
        raise RuntimeError("network unavailable")

    provider._post_chat_completion = raise_error

    narrative = provider.generate(analyze_sample_sales_data())

    assert narrative.mode == "openrouter_fallback"
    assert any(
        "OpenRouter provider error" in warning
        for warning in narrative.warnings
    )


def test_successful_openrouter_response_uses_provider_content() -> None:
    provider = OpenRouterNarrativeProvider(
        AppSettings(openrouter_api_key="test-key")
    )
    provider._post_chat_completion = lambda analysis: {
        "choices": [{"message": {"content": "Provider-written narrative."}}]
    }

    narrative = provider.generate(analyze_sample_sales_data())

    assert narrative.mode == "openrouter"
    assert narrative.narrative == "Provider-written narrative."
    assert narrative.source_evidence.total_orders == 3
