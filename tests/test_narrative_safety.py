from insightops.narrative.safety import (
    get_llm_block_reason,
    should_allow_llm_narrative,
)
from tests.test_markdown_report import _minimal_analysis_response


def test_should_allow_llm_narrative_false_when_human_review_required() -> None:
    analysis = _minimal_analysis_response()
    analysis.security.human_review_required = True

    assert should_allow_llm_narrative(analysis) is False
    assert get_llm_block_reason(analysis) is not None


def test_should_allow_llm_narrative_false_when_prompt_injection_detected() -> None:
    analysis = _minimal_analysis_response()
    analysis.security.prompt_injection_detected = True

    assert should_allow_llm_narrative(analysis) is False
    assert get_llm_block_reason(analysis) is not None


def test_should_allow_llm_narrative_true_for_safe_analysis() -> None:
    analysis = _minimal_analysis_response()
    analysis.quality_gate.can_generate_llm_narrative = True

    assert should_allow_llm_narrative(analysis) is True
    assert get_llm_block_reason(analysis) is None


def test_should_allow_llm_narrative_false_when_quality_gate_blocks() -> None:
    analysis = _minimal_analysis_response()
    analysis.quality_gate.can_generate_llm_narrative = False
    analysis.quality_gate.status = "warning"
    analysis.quality_gate.confidence_level = "medium"

    assert should_allow_llm_narrative(analysis) is False
    assert "data quality gate" in get_llm_block_reason(analysis)
