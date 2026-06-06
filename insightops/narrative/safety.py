from insightops.api.contracts import AnalysisResponse


def should_allow_llm_narrative(analysis: AnalysisResponse) -> bool:
    return get_llm_block_reason(analysis) is None


def get_llm_block_reason(analysis: AnalysisResponse) -> str | None:
    if not analysis.quality_gate.can_generate_llm_narrative:
        return (
            "LLM narrative blocked by the data quality gate "
            f"({analysis.quality_gate.status}, "
            f"{analysis.quality_gate.confidence_level} confidence)."
        )

    if analysis.security.human_review_required:
        return "LLM narrative blocked because human security review is required."

    if analysis.security.prompt_injection_detected:
        return "LLM narrative blocked because prompt injection was detected."

    return None
