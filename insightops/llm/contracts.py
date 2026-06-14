from collections.abc import AsyncIterator
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field


ChatRole = Literal["system", "user", "assistant"]


class ChatMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: ChatRole
    content: str = Field(min_length=1)


class LLMTextResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    model: str
    provider: str


class LLMStreamChunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    token: str
    model: str
    provider: str


class StreamingChatProvider(Protocol):
    def stream_chat_completion(
        self,
        messages: list[ChatMessage],
    ) -> AsyncIterator[str]:
        pass
