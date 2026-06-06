from insightops.narrative.openrouter_provider import OpenRouterNarrativeProvider
from insightops.narrative.service import generate_guarded_narrative
from tests.test_markdown_report import _minimal_analysis_response


def test_safety_blocked_analysis_never_calls_openrouter(monkeypatch) -> None:
    analysis = _minimal_analysis_response()
    analysis.security.human_review_required = True
    calls = {"count": 0}

    class CountingProvider(OpenRouterNarrativeProvider):
        def generate(self, analysis):
            calls["count"] += 1
            return super().generate(analysis)

    monkeypatch.setattr(
        "insightops.narrative.service.get_narrative_provider",
        lambda: CountingProvider(),
    )

    narrative = generate_guarded_narrative(analysis)

    assert narrative.mode == "blocked_fallback"
    assert calls["count"] == 0
