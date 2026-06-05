import os

from insightops.narrative.providers import (
    DeterministicNarrativeProvider,
    DisabledNarrativeProvider,
    NarrativeProvider,
)


def get_narrative_provider(
    provider_name: str | None = None,
) -> NarrativeProvider:
    selected_provider = (
        provider_name
        if provider_name is not None
        else os.getenv("INSIGHTOPS_NARRATIVE_PROVIDER", "disabled")
    )

    match selected_provider.casefold():
        case "deterministic":
            return DeterministicNarrativeProvider()
        case "disabled":
            return DisabledNarrativeProvider()
        case _:
            return DisabledNarrativeProvider()
