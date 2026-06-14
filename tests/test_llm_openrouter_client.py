import asyncio
from types import SimpleNamespace

import pytest

from insightops.config import AppSettings, load_app_settings
from insightops.llm import ChatMessage, LLMProviderError, OpenRouterClient


def test_openrouter_client_requires_api_key_without_injected_client() -> None:
    with pytest.raises(LLMProviderError, match="API key"):
        OpenRouterClient(settings=AppSettings(openrouter_api_key=None))


def test_standard_openrouter_api_key_env_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("INSIGHTOPS_OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "standard-key")

    settings = load_app_settings()

    assert settings.openrouter_api_key == "standard-key"


def test_complete_chat_returns_text_response() -> None:
    client = OpenRouterClient(
        settings=AppSettings(openrouter_api_key=None, openrouter_model="test-model"),
        async_client=_FakeOpenRouterSdk(response_text="Provider text."),
    )

    response = asyncio.run(
        client.complete_chat([ChatMessage(role="user", content="Summarize revenue.")])
    )

    assert response.text == "Provider text."
    assert response.model == "test-model"
    assert response.provider == "openrouter"


def test_stream_chat_completion_yields_delta_tokens() -> None:
    client = OpenRouterClient(
        settings=AppSettings(openrouter_api_key=None),
        async_client=_FakeOpenRouterSdk(stream_tokens=["Revenue", " increased", "."]),
    )

    tokens = asyncio.run(
        _collect_stream(
            client,
            [ChatMessage(role="user", content="Show revenue trend.")],
        )
    )

    assert tokens == ["Revenue", " increased", "."]


def test_stream_chat_completion_wraps_provider_errors() -> None:
    client = OpenRouterClient(
        settings=AppSettings(openrouter_api_key=None),
        async_client=_FailingOpenRouterSdk(),
    )

    with pytest.raises(LLMProviderError, match="streaming request failed"):
        asyncio.run(
            _collect_stream(
                client,
                [ChatMessage(role="user", content="Show revenue trend.")],
            )
        )


async def _collect_stream(
    client: OpenRouterClient,
    messages: list[ChatMessage],
) -> list[str]:
    return [token async for token in client.stream_chat_completion(messages)]


class _FakeOpenRouterSdk:
    def __init__(
        self,
        *,
        response_text: str = "",
        stream_tokens: list[str] | None = None,
    ) -> None:
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(
                create=self._create,
            )
        )
        self._response_text = response_text
        self._stream_tokens = stream_tokens or []

    async def _create(self, *, stream: bool, **_kwargs):
        if stream:
            return _FakeAsyncStream(self._stream_tokens)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self._response_text),
                )
            ]
        )


class _FailingOpenRouterSdk:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(
                create=self._create,
            )
        )

    async def _create(self, **_kwargs):
        raise TimeoutError("provider timed out")


class _FakeAsyncStream:
    def __init__(self, tokens: list[str]) -> None:
        self._tokens = tokens

    def __aiter__(self):
        self._index = 0
        return self

    async def __anext__(self):
        if self._index >= len(self._tokens):
            raise StopAsyncIteration
        token = self._tokens[self._index]
        self._index += 1
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content=token),
                )
            ]
        )
