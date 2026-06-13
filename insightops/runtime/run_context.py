from dataclasses import dataclass
from pathlib import Path
from typing import Any

from insightops.conversation.context import ConversationContext
from insightops.datasets.models import DatasetMetadata


@dataclass(frozen=True)
class RunContext:
    run_id: str
    dataset_id: str
    message: str
    schema: list[Any]
    preview_rows: list[Any]
    conversation_id: str | None = None
    conversation_context: ConversationContext | None = None
    dataset_metadata: DatasetMetadata | None = None
    dataset_path: Path | None = None
