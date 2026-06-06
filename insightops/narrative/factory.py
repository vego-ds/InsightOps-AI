import os

from insightops.config import load_app_settings
from insightops.narrative.openrouter_provider import OpenRouterNarrativeProvider
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
        else os.getenv(
            "INSIGHTOPS_NARRATIVE_PROVIDER",
            load_app_settings().narrative_provider,
        )
    )

    match selected_provider.casefold():
        case "deterministic":
            return DeterministicNarrativeProvider()
        case "disabled":
            return DisabledNarrativeProvider()
        case "openrouter":
            return OpenRouterNarrativeProvider()
        case _:
            return DisabledNarrativeProvider()
