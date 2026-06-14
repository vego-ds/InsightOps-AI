from collections.abc import AsyncIterator, Sequence
from typing import Any

from insightops.config import AppSettings, load_app_settings
from insightops.llm.contracts import ChatMessage, LLMTextResponse


OPENROUTER_PROVIDER = "openrouter"
OPENROUTER_TITLE = "InsightOps AI"
OPENROUTER_REFERER = "https://insightops.ai"


class LLMProviderError(RuntimeError):
    pass


class OpenRouterClient:
    def __init__(
        self,
        *,
        settings: AppSettings | None = None,
        async_client: Any | None = None,
        referer: str = OPENROUTER_REFERER,
        title: str = OPENROUTER_TITLE,
    ) -> None:
        self.settings = settings or load_app_settings()
        self.model = self.settings.openrouter_model
        self._client = async_client or self._build_async_client(
            referer=referer,
            title=title,
        )

    async def complete_chat(
        self,
        messages: list[ChatMessage],
    ) -> LLMTextResponse:
        self._validate_messages(messages)
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=_serialize_messages(messages),
                stream=False,
            )
            text = _extract_completion_text(response)
        except _provider_exceptions() as error:
            raise LLMProviderError("OpenRouter completion request failed.") from error
        except (AttributeError, IndexError, TypeError, ValueError) as error:
            raise LLMProviderError("OpenRouter completion response was invalid.") from error

        return LLMTextResponse(
            text=text,
            model=self.model,
            provider=OPENROUTER_PROVIDER,
        )

    async def stream_chat_completion(
        self,
        messages: list[ChatMessage],
    ) -> AsyncIterator[str]:
        self._validate_messages(messages)
        try:
            stream = await self._client.chat.completions.create(
                model=self.model,
                messages=_serialize_messages(messages),
                stream=True,
            )
            async for chunk in stream:
                token = _extract_stream_token(chunk)
                if token:
                    yield token
        except _provider_exceptions() as error:
            raise LLMProviderError("OpenRouter streaming request failed.") from error
        except (AttributeError, IndexError, TypeError, ValueError) as error:
            raise LLMProviderError("OpenRouter streaming response was invalid.") from error

    def _build_async_client(self, *, referer: str, title: str) -> Any:
        if not self.settings.openrouter_api_key:
            raise LLMProviderError("OpenRouter API key is not configured.")

        try:
            from openai import AsyncOpenAI
        except ImportError as error:
            raise LLMProviderError("The openai SDK is not installed.") from error

        return AsyncOpenAI(
            api_key=self.settings.openrouter_api_key,
            base_url=self.settings.openrouter_base_url,
            default_headers={
                "HTTP-Referer": referer,
                "X-OpenRouter-Title": title,
            },
        )

    @staticmethod
    def _validate_messages(messages: Sequence[ChatMessage]) -> None:
        if not messages:
            raise LLMProviderError("At least one chat message is required.")


def _serialize_messages(messages: Sequence[ChatMessage]) -> list[dict[str, str]]:
    return [message.model_dump() for message in messages]


def _extract_completion_text(response: Any) -> str:
    content = response.choices[0].message.content
    if not isinstance(content, str) or not content.strip():
        raise ValueError("completion text is empty")
    return content.strip()


def _extract_stream_token(chunk: Any) -> str:
    delta = chunk.choices[0].delta
    content = getattr(delta, "content", None)
    return content if isinstance(content, str) else ""


def _provider_exceptions() -> tuple[type[Exception], ...]:
    try:
        from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAIError
    except ImportError:
        return (TimeoutError, OSError)

    return (
        APIConnectionError,
        APIStatusError,
        APITimeoutError,
        OpenAIError,
        TimeoutError,
        OSError,
    )
