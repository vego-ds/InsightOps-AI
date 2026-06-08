import json
from urllib import request

from insightops.api.contracts import AnalysisResponse
from insightops.config import AppSettings, load_app_settings
from insightops.narrative.contracts import ExecutiveNarrative
from insightops.narrative.prompt_builder import build_guarded_narrative_prompt
from insightops.narrative.writer import generate_deterministic_narrative


class OpenRouterNarrativeProvider:
    def __init__(self, settings: AppSettings | None = None) -> None:
        self.settings = settings or load_app_settings()

    def generate(self, analysis: AnalysisResponse) -> ExecutiveNarrative:
        if not self.settings.openrouter_api_key:
            return _fallback_narrative(
                analysis,
                "openrouter_missing_key_fallback",
                "Missing OpenRouter API key.",
            )

        try:
            response = self._post_chat_completion(analysis)
            content = response["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                return _fallback_narrative(
                    analysis,
                    "openrouter_fallback",
                    "Malformed provider response.",
                )
        except (KeyError, IndexError, TypeError, ValueError) as error:
            return _fallback_narrative(
                analysis,
                "openrouter_fallback",
                f"Malformed provider response: {error}",
            )
        except Exception as error:
            return _fallback_narrative(
                analysis,
                "openrouter_fallback",
                f"OpenRouter provider error: {error}",
            )

        narrative = generate_deterministic_narrative(analysis)
        narrative.mode = "openrouter"
        narrative.narrative = content.strip()
        return narrative

    def _post_chat_completion(self, analysis: AnalysisResponse) -> dict:
        payload = {
            "model": self.settings.openrouter_model,
            "messages": _messages_for_analysis(analysis),
            "temperature": 0.2,
            "max_tokens": 500,
            "stream": False,
        }
        api_request = request.Request(
            f"{self.settings.openrouter_base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with request.urlopen(api_request, timeout=30) as response:
            response_body = response.read().decode("utf-8")

        parsed_response = json.loads(response_body)
        if not isinstance(parsed_response, dict):
            raise ValueError("provider response must be an object")
        return parsed_response


def _messages_for_analysis(analysis: AnalysisResponse) -> list[dict[str, str]]:
    prompt = build_guarded_narrative_prompt(analysis)
    instructions, facts = prompt.split(
        "UNTRUSTED DATA AND DETERMINISTIC FACTS:",
        maxsplit=1,
    )

    return [
        {"role": "system", "content": instructions.strip()},
        {
            "role": "user",
            "content": (f"UNTRUSTED DATA AND DETERMINISTIC FACTS:{facts}").strip(),
        },
    ]


def _fallback_narrative(
    analysis: AnalysisResponse,
    mode: str,
    warning: str,
) -> ExecutiveNarrative:
    narrative = generate_deterministic_narrative(analysis)
    narrative.mode = mode
    narrative.warnings.append(warning)
    return narrative
