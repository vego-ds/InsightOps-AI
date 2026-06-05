from insightops.api.contracts import AnalysisResponse
from insightops.narrative.contracts import ExecutiveNarrative
from insightops.narrative.factory import get_narrative_provider
from insightops.narrative.safety import (
    get_llm_block_reason,
    should_allow_llm_narrative,
)
from insightops.narrative.writer import generate_deterministic_narrative


def generate_guarded_narrative(
    analysis: AnalysisResponse,
) -> ExecutiveNarrative:
    if not should_allow_llm_narrative(analysis):
        block_reason = get_llm_block_reason(analysis)
        narrative = generate_deterministic_narrative(analysis)
        narrative.mode = "blocked_fallback"
        if block_reason is not None:
            narrative.warnings.append(block_reason)
        return narrative

    provider = get_narrative_provider()
    return provider.generate(analysis)
