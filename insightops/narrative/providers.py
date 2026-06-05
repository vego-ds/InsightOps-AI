from typing import Protocol

from insightops.api.contracts import AnalysisResponse
from insightops.narrative.contracts import ExecutiveNarrative
from insightops.narrative.writer import generate_deterministic_narrative


class NarrativeProvider(Protocol):
    def generate(self, analysis: AnalysisResponse) -> ExecutiveNarrative:
        pass


class DisabledNarrativeProvider:
    def generate(self, analysis: AnalysisResponse) -> ExecutiveNarrative:
        narrative = generate_deterministic_narrative(analysis)
        narrative.mode = "disabled_fallback"
        return narrative


class DeterministicNarrativeProvider:
    def generate(self, analysis: AnalysisResponse) -> ExecutiveNarrative:
        narrative = generate_deterministic_narrative(analysis)
        narrative.mode = "deterministic"
        return narrative
