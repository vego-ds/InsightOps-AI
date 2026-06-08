SUSPICIOUS_PROMPT_INJECTION_PHRASES = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "bypass validation",
    "disable safety",
    "reveal secrets",
    "show api key",
    "print api key",
    "system prompt",
    "developer message",
    "override instructions",
)


def detect_prompt_injection(text: str) -> bool:
    normalized_text = text.casefold()
    return any(
        phrase in normalized_text for phrase in SUSPICIOUS_PROMPT_INJECTION_PHRASES
    )
