from insightops.narrative.factory import get_narrative_provider
from insightops.narrative.service import generate_guarded_narrative
from insightops.narrative.writer import generate_deterministic_narrative
from insightops.pipeline.sample_analysis import analyze_sample_sales_data
from tests.test_markdown_report import _minimal_analysis_response


def test_deterministic_narrative_generation_works() -> None:
    narrative = generate_deterministic_narrative(analyze_sample_sales_data())

    assert narrative.mode == "deterministic"
    assert narrative.title == "Executive Sales Narrative"
    assert narrative.narrative


def test_narrative_includes_kpi_and_validation_facts() -> None:
    narrative = generate_deterministic_narrative(analyze_sample_sales_data())

    assert "$4700.00" in narrative.narrative
    assert "3 orders" in narrative.narrative
    assert "2 invalid rows out of 5" in narrative.narrative


def test_narrative_includes_anomaly_warnings_when_anomalies_exist() -> None:
    analysis = _minimal_analysis_response()
    analysis.anomalies.total_anomalies = 1

    narrative = generate_deterministic_narrative(analysis)

    assert "Sales anomalies require investigation." in narrative.warnings


def test_narrative_includes_security_warning_when_human_review_required() -> None:
    analysis = _minimal_analysis_response()
    analysis.security.human_review_required = True
    analysis.security.prompt_injection_detected = True

    narrative = generate_deterministic_narrative(analysis)

    assert "Security scan requires human review." in narrative.warnings


def test_source_evidence_is_populated() -> None:
    narrative = generate_deterministic_narrative(analyze_sample_sales_data())

    assert narrative.source_evidence.total_orders == 3
    assert narrative.source_evidence.invalid_rows == 2
    assert narrative.source_evidence.insight_count > 0


def test_default_provider_works_without_environment_variables(monkeypatch) -> None:
    monkeypatch.delenv("INSIGHTOPS_NARRATIVE_PROVIDER", raising=False)

    provider = get_narrative_provider()
    narrative = provider.generate(analyze_sample_sales_data())

    assert narrative.mode == "disabled_fallback"


def test_unknown_provider_safely_falls_back_to_disabled_provider() -> None:
    provider = get_narrative_provider("unknown")
    narrative = provider.generate(analyze_sample_sales_data())

    assert narrative.mode == "disabled_fallback"


def test_blocked_narrative_returns_blocked_fallback() -> None:
    analysis = _minimal_analysis_response()
    analysis.security.human_review_required = True

    narrative = generate_guarded_narrative(analysis)

    assert narrative.mode == "blocked_fallback"
    assert narrative.warnings
