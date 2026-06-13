from insightops.conversation.context import ConversationContext
from insightops.planning.intents import AnalysisPlan


class ConversationStore:
    def __init__(self) -> None:
        self._contexts: dict[str, ConversationContext] = {}

    def get_or_create(
        self,
        conversation_id: str,
        dataset_id: str | None = None,
    ) -> ConversationContext:
        context = self._contexts.get(conversation_id)
        if context is not None and dataset_id is not None and context.dataset_id not in {None, dataset_id}:
            context = ConversationContext(
                conversation_id=conversation_id,
                dataset_id=dataset_id,
            )
            self._contexts[conversation_id] = context
        if context is None:
            context = ConversationContext(
                conversation_id=conversation_id,
                dataset_id=dataset_id,
            )
            self._contexts[conversation_id] = context
        elif dataset_id is not None and context.dataset_id is None:
            context.dataset_id = dataset_id
        return context

    def update_after_plan(
        self,
        *,
        conversation_id: str,
        dataset_id: str,
        run_id: str,
        plan: AnalysisPlan,
    ) -> ConversationContext:
        context = self.get_or_create(conversation_id, dataset_id)
        context.dataset_id = dataset_id
        context.last_run_id = run_id
        context.last_intent = plan.intent.value
        context.last_x_column = plan.x_column
        context.last_y_column = plan.y_column
        context.last_requested_columns = list(plan.requested_columns)
        return context

    def update_after_artifacts(
        self,
        *,
        conversation_id: str,
        artifact_ids: list[str],
        artifact_kinds: list[str],
    ) -> ConversationContext:
        context = self.get_or_create(conversation_id)
        context.last_artifact_ids = artifact_ids
        context.last_artifact_kinds = artifact_kinds
        return context

    def clear(self, conversation_id: str) -> None:
        self._contexts.pop(conversation_id, None)


conversation_store = ConversationStore()
