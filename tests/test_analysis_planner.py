import asyncio

from insightops.config import AppSettings
from insightops.llm import ChatMessage, LLMProviderError, LLMTextResponse
from insightops.planning import (
    AnalysisIntent,
    build_analysis_plan,
    build_hybrid_analysis_plan,
    resolve_column,
)


SCHEMA = [
    {"key": "region", "label": "Region", "dataType": "string"},
    {"key": "product", "label": "Product", "dataType": "string"},
    {"key": "order_date", "label": "Order Date", "dataType": "date"},
    {"key": "revenue", "label": "Revenue", "dataType": "number"},
]


def test_planner_detects_dataset_summary() -> None:
    plan = build_analysis_plan("Give me an overview", SCHEMA)

    assert plan.intent == AnalysisIntent.dataset_summary


def test_planner_detects_missing_values() -> None:
    plan = build_analysis_plan("Show missing and null values", SCHEMA)

    assert plan.intent == AnalysisIntent.missing_values


def test_planner_detects_grouped_metric_for_revenue_by_region() -> None:
    plan = build_analysis_plan("revenue by region", SCHEMA)

    assert plan.intent == AnalysisIntent.grouped_metric
    assert plan.x_column == "region"
    assert plan.y_column == "revenue"


def test_planner_detects_top_categories_for_top_product() -> None:
    plan = build_analysis_plan("top product", SCHEMA)

    assert plan.intent == AnalysisIntent.top_categories
    assert plan.x_column == "product"


def test_planner_detects_trend_over_time() -> None:
    plan = build_analysis_plan("revenue over time", SCHEMA)

    assert plan.intent == AnalysisIntent.trend_over_time
    assert plan.x_column == "order_date"
    assert plan.y_column == "revenue"


def test_column_resolver_maps_sales_to_revenue_when_revenue_exists() -> None:
    assert resolve_column("sales", SCHEMA, preferred_type="number") == "revenue"


def test_hybrid_planner_uses_llm_plan_when_configured() -> None:
    plan = asyncio.run(
        build_hybrid_analysis_plan(
            "Compare income by market",
            SCHEMA,
            settings=AppSettings(openrouter_api_key="test-key"),
            llm_client=_FakePlannerClient(
                '{"intent":"grouped_metric","x_column":"region",'
                '"y_column":"revenue","explanation":"Grouped revenue by region."}'
            ),
        )
    )

    assert plan.intent == AnalysisIntent.grouped_metric
    assert plan.x_column == "region"
    assert plan.y_column == "revenue"
    assert "LLM-assisted planner" in plan.explanation


def test_hybrid_planner_falls_back_without_api_key() -> None:
    plan = asyncio.run(
        build_hybrid_analysis_plan(
            "revenue by region",
            SCHEMA,
            settings=AppSettings(openrouter_api_key=None),
        )
    )

    assert plan.intent == AnalysisIntent.grouped_metric
    assert plan.x_column == "region"
    assert plan.y_column == "revenue"


def test_hybrid_planner_falls_back_on_provider_error() -> None:
    plan = asyncio.run(
        build_hybrid_analysis_plan(
            "Show missing values",
            SCHEMA,
            settings=AppSettings(openrouter_api_key="test-key"),
            llm_client=_FailingPlannerClient(),
        )
    )

    assert plan.intent == AnalysisIntent.missing_values


def test_hybrid_planner_does_not_use_invented_columns() -> None:
    plan = asyncio.run(
        build_hybrid_analysis_plan(
            "revenue by region",
            SCHEMA,
            settings=AppSettings(openrouter_api_key="test-key"),
            llm_client=_FakePlannerClient(
                '{"intent":"grouped_metric","x_column":"made_up",'
                '"y_column":"fake_metric","explanation":"Invalid columns."}'
            ),
        )
    )

    assert plan.intent == AnalysisIntent.grouped_metric
    assert plan.x_column == "region"
    assert plan.y_column == "revenue"


class _FakePlannerClient:
    def __init__(self, text: str) -> None:
        self._text = text

    async def complete_chat(self, messages: list[ChatMessage]) -> LLMTextResponse:
        assert messages
        return LLMTextResponse(
            text=self._text,
            model="test-model",
            provider="openrouter",
        )


class _FailingPlannerClient:
    async def complete_chat(self, messages: list[ChatMessage]) -> LLMTextResponse:
        raise LLMProviderError("provider unavailable")
