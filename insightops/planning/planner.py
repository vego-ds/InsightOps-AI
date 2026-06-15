import json
import re
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from insightops.config import AppSettings, load_app_settings
from insightops.llm import ChatMessage, LLMProviderError, LLMTextResponse, OpenRouterClient
from insightops.planning.column_resolver import resolve_column, resolve_first_by_types
from insightops.planning.intents import AnalysisIntent, AnalysisPlan

Schema = list[dict[str, Any]]

BY_PATTERN = re.compile(r"\bby\s+([a-zA-Z0-9_ -]+)", flags=re.IGNORECASE)
TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")
JSON_BLOCK_PATTERN = re.compile(r"```(?:json)?\s*(.*?)\s*```", flags=re.DOTALL)

MISSING_KEYWORDS = frozenset({"missing", "null", "empty", "blanks"})
TREND_KEYWORDS = frozenset({"trend", "time", "date", "monthly", "daily"})
TOP_CATEGORY_KEYWORDS = frozenset({"top", "best", "highest", "most"})
NUMERIC_SUMMARY_KEYWORDS = frozenset(
    {"numeric", "statistics", "mean", "average", "min", "max"},
)
DATASET_SUMMARY_KEYWORDS = frozenset({"summary", "overview", "profile"})

DATASET_SUMMARY_BUILDERS = [
    "build_dataset_profile_table",
    "build_basic_chart_artifact",
    "build_markdown_summary_artifact",
]
MISSING_VALUES_BUILDERS = [
    "build_missing_values_table",
    "build_markdown_summary_artifact",
]
NUMERIC_SUMMARY_BUILDERS = [
    "build_numeric_summary_table",
    "build_markdown_summary_artifact",
]
GROUPED_METRIC_BUILDERS = [
    "build_grouped_metric_table",
    "build_grouped_metric_chart",
    "build_markdown_summary_artifact",
]
TOP_CATEGORIES_BUILDERS = [
    "build_top_categories_table",
    "build_grouped_metric_chart",
    "build_markdown_summary_artifact",
]
TREND_BUILDERS = [
    "build_trend_table",
    "build_trend_chart",
    "build_markdown_summary_artifact",
]

BUILDERS_BY_INTENT = {
    AnalysisIntent.dataset_summary: DATASET_SUMMARY_BUILDERS,
    AnalysisIntent.missing_values: MISSING_VALUES_BUILDERS,
    AnalysisIntent.numeric_summary: NUMERIC_SUMMARY_BUILDERS,
    AnalysisIntent.grouped_metric: GROUPED_METRIC_BUILDERS,
    AnalysisIntent.top_categories: TOP_CATEGORIES_BUILDERS,
    AnalysisIntent.trend_over_time: TREND_BUILDERS,
    AnalysisIntent.unknown: DATASET_SUMMARY_BUILDERS,
}

TITLES_BY_INTENT = {
    AnalysisIntent.dataset_summary: "Dataset Summary",
    AnalysisIntent.missing_values: "Missing Values",
    AnalysisIntent.numeric_summary: "Numeric Summary",
    AnalysisIntent.grouped_metric: "Grouped Metric",
    AnalysisIntent.top_categories: "Top Categories",
    AnalysisIntent.trend_over_time: "Trend Over Time",
    AnalysisIntent.unknown: "Dataset Summary",
}


class PlannerLLMClient(Protocol):
    async def complete_chat(self, messages: list[ChatMessage]) -> LLMTextResponse:
        pass


class _LLMPlanPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    intent: AnalysisIntent
    x_column: str | None = None
    y_column: str | None = None
    explanation: str = Field(default="LLM-assisted routing selected a plan.")


def build_analysis_plan(message: str, schema: Schema) -> AnalysisPlan:
    prompt = message.casefold()

    if _contains(prompt, MISSING_KEYWORDS):
        return _plan(
            intent=AnalysisIntent.missing_values,
            title="Missing Values",
            artifact_builders=MISSING_VALUES_BUILDERS,
            explanation="Prompt requested missing, null, empty, or blank value analysis.",
        )

    if _contains(prompt, TREND_KEYWORDS):
        x_column = _resolve_time_column(schema)
        y_column = _resolve_metric_from_prompt(message, schema)
        return _plan(
            intent=AnalysisIntent.trend_over_time,
            title="Trend Over Time",
            artifact_builders=TREND_BUILDERS,
            x_column=x_column,
            y_column=y_column,
            explanation="Prompt requested time, date, daily, monthly, or trend analysis.",
        )

    by_match = BY_PATTERN.search(message)
    if by_match:
        x_column = resolve_column(by_match.group(1), schema, preferred_type="string")
        y_column = _resolve_metric_from_prompt(message[: by_match.start()], schema)
        return _plan(
            intent=AnalysisIntent.grouped_metric,
            title="Grouped Metric",
            artifact_builders=GROUPED_METRIC_BUILDERS,
            x_column=x_column,
            y_column=y_column,
            explanation='Prompt matched a deterministic "by <column>" grouping pattern.',
        )

    if _contains(prompt, TOP_CATEGORY_KEYWORDS):
        x_column = _resolve_category_from_prompt(message, schema)
        y_column = _resolve_metric_from_prompt(message, schema)
        return _plan(
            intent=AnalysisIntent.top_categories,
            title="Top Categories",
            artifact_builders=TOP_CATEGORIES_BUILDERS,
            x_column=x_column,
            y_column=y_column,
            explanation="Prompt requested top, best, highest, or most categories.",
        )

    if _contains(prompt, NUMERIC_SUMMARY_KEYWORDS):
        return _plan(
            intent=AnalysisIntent.numeric_summary,
            title="Numeric Summary",
            artifact_builders=NUMERIC_SUMMARY_BUILDERS,
            explanation="Prompt requested numeric statistics.",
        )

    if _contains(prompt, DATASET_SUMMARY_KEYWORDS):
        return _dataset_summary_plan("Prompt requested summary, overview, or profile.")

    return _dataset_summary_plan(
        "Prompt did not match a specific intent; using safe dataset summary.",
    )


async def build_hybrid_analysis_plan(
    message: str,
    schema: Schema,
    *,
    llm_client: PlannerLLMClient | None = None,
    settings: AppSettings | None = None,
) -> AnalysisPlan:
    fallback_plan = build_analysis_plan(message, schema)
    active_settings = settings or load_app_settings()
    if llm_client is None and not active_settings.openrouter_api_key:
        return fallback_plan

    try:
        client = llm_client or OpenRouterClient(settings=active_settings)
        response = await client.complete_chat(_planner_messages(message, schema))
        return _plan_from_llm_response(
            response.text,
            message=message,
            schema=schema,
            fallback_plan=fallback_plan,
        )
    except (
        LLMProviderError,
        ValidationError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):
        return fallback_plan


def _dataset_summary_plan(explanation: str) -> AnalysisPlan:
    return _plan(
        intent=AnalysisIntent.dataset_summary,
        title="Dataset Summary",
        artifact_builders=DATASET_SUMMARY_BUILDERS,
        explanation=explanation,
    )


def _plan(
    *,
    intent: AnalysisIntent,
    title: str,
    artifact_builders: list[str],
    explanation: str,
    x_column: str | None = None,
    y_column: str | None = None,
) -> AnalysisPlan:
    return AnalysisPlan(
        intent=intent,
        title=title,
        requested_columns=_requested_columns(x_column, y_column),
        artifact_builders=artifact_builders,
        x_column=x_column,
        y_column=y_column,
        explanation=explanation,
    )


def _requested_columns(*columns: str | None) -> list[str]:
    return [column for column in columns if column]


def _resolve_time_column(schema: Schema) -> str | None:
    return resolve_column("date", schema, preferred_type="date") or resolve_first_by_types(
        schema,
        {"date", "datetime"},
    )


def _resolve_metric_from_prompt(message: str, schema: Schema) -> str | None:
    return _resolve_first_prompt_column(message, schema) or resolve_column(
        "sales",
        schema,
        preferred_type="number",
    ) or resolve_first_by_types(schema, {"number", "integer"})


def _resolve_category_from_prompt(message: str, schema: Schema) -> str | None:
    return _resolve_first_prompt_column(message, schema) or resolve_first_by_types(
        schema,
        {"string", "categorical", "boolean"},
    )


def _resolve_first_prompt_column(message: str, schema: Schema) -> str | None:
    for token in TOKEN_PATTERN.findall(message):
        matched = resolve_column(token, schema)
        if matched:
            return matched
    return None


def _contains(prompt: str, keywords: frozenset[str]) -> bool:
    return any(keyword in prompt for keyword in keywords)


def _planner_messages(message: str, schema: Schema) -> list[ChatMessage]:
    return [
        ChatMessage(
            role="system",
            content=(
                "You route data-analysis prompts into one JSON plan. "
                "Return only JSON with keys: intent, x_column, y_column, explanation. "
                "Allowed intents: dataset_summary, missing_values, numeric_summary, "
                "grouped_metric, top_categories, trend_over_time, unknown. "
                "Use only column keys from the provided schema. Use null when no "
                "column is required or a safe column is unavailable. Do not write code."
            ),
        ),
        ChatMessage(
            role="user",
            content=json.dumps(
                {
                    "message": message,
                    "schema": _compact_schema(schema),
                },
                separators=(",", ":"),
            ),
        ),
    ]


def _compact_schema(schema: Schema) -> list[dict[str, str]]:
    compact: list[dict[str, str]] = []
    for column in schema:
        key = column.get("key")
        if not isinstance(key, str) or not key:
            continue
        label = column.get("label")
        data_type = column.get("dataType")
        compact.append(
            {
                "key": key,
                "label": label if isinstance(label, str) and label else key,
                "dataType": data_type if isinstance(data_type, str) else "unknown",
            }
        )
    return compact


def _plan_from_llm_response(
    response_text: str,
    *,
    message: str,
    schema: Schema,
    fallback_plan: AnalysisPlan,
) -> AnalysisPlan:
    payload = _LLMPlanPayload.model_validate_json(_extract_json_payload(response_text))
    if payload.intent is AnalysisIntent.unknown:
        return fallback_plan

    x_column = _resolve_llm_column(payload.x_column, schema)
    y_column = _resolve_llm_column(payload.y_column, schema)

    if payload.intent is AnalysisIntent.trend_over_time:
        x_column = x_column or fallback_plan.x_column or _resolve_time_column(schema)
        y_column = y_column or fallback_plan.y_column or _resolve_metric_from_prompt(
            message,
            schema,
        )
    elif payload.intent in {
        AnalysisIntent.grouped_metric,
        AnalysisIntent.top_categories,
    }:
        x_column = x_column or fallback_plan.x_column or _resolve_category_from_prompt(
            message,
            schema,
        )
        y_column = y_column or fallback_plan.y_column or _resolve_metric_from_prompt(
            message,
            schema,
        )

    return _plan(
        intent=payload.intent,
        title=TITLES_BY_INTENT[payload.intent],
        artifact_builders=BUILDERS_BY_INTENT[payload.intent],
        x_column=x_column,
        y_column=y_column,
        explanation=_llm_explanation(payload.explanation),
    )


def _extract_json_payload(response_text: str) -> str:
    text = response_text.strip()
    match = JSON_BLOCK_PATTERN.fullmatch(text)
    return match.group(1).strip() if match else text


def _resolve_llm_column(column: str | None, schema: Schema) -> str | None:
    if column is None:
        return None
    return resolve_column(column, schema)


def _llm_explanation(explanation: str) -> str:
    clean = " ".join(explanation.split())
    if not clean:
        return "LLM-assisted planner selected a validated intent."
    return f"LLM-assisted planner selected a validated intent. {clean[:240]}"
