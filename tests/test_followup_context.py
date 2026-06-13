from insightops.conversation import ConversationStore, resolve_followup_plan
from insightops.planning import AnalysisIntent, build_analysis_plan


SCHEMA = [
    {"key": "region", "label": "Region", "dataType": "string"},
    {"key": "product", "label": "Product", "dataType": "string"},
    {"key": "order_date", "label": "Order Date", "dataType": "date"},
    {"key": "revenue", "label": "Revenue", "dataType": "number"},
    {"key": "quantity", "label": "Quantity", "dataType": "integer"},
]


def test_followup_now_by_product_reuses_last_revenue_metric() -> None:
    store = ConversationStore()
    initial_plan = build_analysis_plan("revenue by region", SCHEMA)
    context = store.update_after_plan(
        conversation_id="conv-1",
        dataset_id="dataset-1",
        run_id="run-1",
        plan=initial_plan,
    )

    plan = resolve_followup_plan(
        message="now by product",
        schema=SCHEMA,
        context=context,
    )

    assert plan.intent == AnalysisIntent.grouped_metric
    assert plan.x_column == "product"
    assert plan.y_column == "revenue"


def test_followup_over_time_reuses_revenue_and_resolves_date_column() -> None:
    store = ConversationStore()
    context = store.update_after_plan(
        conversation_id="conv-1",
        dataset_id="dataset-1",
        run_id="run-1",
        plan=build_analysis_plan("revenue by region", SCHEMA),
    )

    plan = resolve_followup_plan(
        message="over time",
        schema=SCHEMA,
        context=context,
    )

    assert plan.intent == AnalysisIntent.trend_over_time
    assert plan.x_column == "order_date"
    assert plan.y_column == "revenue"


def test_explicit_quantity_by_region_overrides_previous_revenue() -> None:
    store = ConversationStore()
    context = store.update_after_plan(
        conversation_id="conv-1",
        dataset_id="dataset-1",
        run_id="run-1",
        plan=build_analysis_plan("revenue by product", SCHEMA),
    )

    plan = resolve_followup_plan(
        message="quantity by region",
        schema=SCHEMA,
        context=context,
    )

    assert plan.intent == AnalysisIntent.grouped_metric
    assert plan.x_column == "region"
    assert plan.y_column == "quantity"


def test_unknown_followup_falls_back_safely() -> None:
    store = ConversationStore()
    context = store.get_or_create("conv-1", "dataset-1")

    plan = resolve_followup_plan(
        message="show me something useful",
        schema=SCHEMA,
        context=context,
    )

    assert plan.intent == AnalysisIntent.dataset_summary


def test_missing_values_prompt_overrides_grouped_metric_context() -> None:
    store = ConversationStore()
    context = store.update_after_plan(
        conversation_id="conv-1",
        dataset_id="dataset-1",
        run_id="run-1",
        plan=build_analysis_plan("revenue by product", SCHEMA),
    )

    plan = resolve_followup_plan(
        message="missing values",
        schema=SCHEMA,
        context=context,
    )

    assert plan.intent == AnalysisIntent.missing_values
    assert plan.x_column is None
    assert plan.y_column is None


def test_context_is_scoped_by_conversation_id() -> None:
    store = ConversationStore()
    first = store.update_after_plan(
        conversation_id="conv-1",
        dataset_id="dataset-1",
        run_id="run-1",
        plan=build_analysis_plan("revenue by region", SCHEMA),
    )
    second = store.update_after_plan(
        conversation_id="conv-2",
        dataset_id="dataset-1",
        run_id="run-2",
        plan=build_analysis_plan("quantity by product", SCHEMA),
    )

    assert first.conversation_id == "conv-1"
    assert first.last_y_column == "revenue"
    assert second.conversation_id == "conv-2"
    assert second.last_y_column == "quantity"


def test_context_resets_when_conversation_moves_to_new_dataset() -> None:
    store = ConversationStore()
    store.update_after_plan(
        conversation_id="conv-1",
        dataset_id="dataset-1",
        run_id="run-1",
        plan=build_analysis_plan("revenue by region", SCHEMA),
    )

    context = store.get_or_create("conv-1", "dataset-2")

    assert context.dataset_id == "dataset-2"
    assert context.last_y_column is None
    assert context.last_x_column is None


def test_context_tracks_last_artifact_ids_and_kinds() -> None:
    store = ConversationStore()
    context = store.update_after_artifacts(
        conversation_id="conv-1",
        artifact_ids=["artifact-1", "artifact-2"],
        artifact_kinds=["chart", "table"],
    )

    assert context.last_artifact_ids == ["artifact-1", "artifact-2"]
    assert context.last_artifact_kinds == ["chart", "table"]
