from dataclasses import dataclass, field


@dataclass
class ConversationContext:
    conversation_id: str
    dataset_id: str | None = None
    last_run_id: str | None = None
    last_intent: str | None = None
    last_x_column: str | None = None
    last_y_column: str | None = None
    last_requested_columns: list[str] = field(default_factory=list)
    last_artifact_ids: list[str] = field(default_factory=list)
    last_artifact_kinds: list[str] = field(default_factory=list)
