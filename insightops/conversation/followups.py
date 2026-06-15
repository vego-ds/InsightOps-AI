import re
from typing import Any

from insightops.conversation.context import ConversationContext
from insightops.planning.column_resolver import resolve_column, resolve_first_by_types
from insightops.planning.intents import AnalysisIntent, AnalysisPlan
from insightops.planning.planner import build_analysis_plan, build_hybrid_analysis_plan


def resolve_followup_plan(
    *,
    message: str,
    schema: list[dict[str, Any]],
    context: ConversationContext | None,
) -> AnalysisPlan:
    base_plan = build_analysis_plan(message, schema)
    return _resolve_followup_from_base_plan(
        message=message,
        schema=schema,
        context=context,
        base_plan=base_plan,
    )


async def resolve_hybrid_followup_plan(
    *,
    message: str,
    schema: list[dict[str, Any]],
    context: ConversationContext | None,
) -> AnalysisPlan:
    base_plan = await build_hybrid_analysis_plan(message, schema)
    return _resolve_followup_from_base_plan(
        message=message,
        schema=schema,
        context=context,
        base_plan=base_plan,
    )


def _resolve_followup_from_base_plan(
    *,
    message: str,
    schema: list[dict[str, Any]],
    context: ConversationContext | None,
    base_plan: AnalysisPlan,
) -> AnalysisPlan:
    if context is None:
        return base_plan

    prompt = message.casefold().strip()
    if any(keyword in prompt for keyword in ("missing", "null", "empty", "blanks")):
        return base_plan

    if _has_explicit_metric_and_group(message, schema):
        return base_plan

    by_match = re.fullmatch(r"(now\s+)?by\s+([a-zA-Z0-9_ -]+)", message.strip(), re.IGNORECASE)
    if by_match and context.last_y_column:
        x_column = resolve_column(by_match.group(2), schema, preferred_type="string")
        y_column = resolve_column(context.last_y_column, schema, preferred_type="number")
        if x_column and y_column:
            return _grouped_plan(x_column, y_column, "Follow-up reused previous metric with a new grouping column.")

    if prompt in {"over time", "trend", "trend over time"} and context.last_y_column:
        x_column = resolve_column("date", schema, preferred_type="date") or resolve_first_by_types(
            schema, {"date", "datetime"}
        )
        y_column = resolve_column(context.last_y_column, schema, preferred_type="number")
        if x_column and y_column:
            return _trend_plan(x_column, y_column, "Follow-up reused previous metric over time.")

    about_match = re.fullmatch(r"what about\s+([a-zA-Z0-9_ -]+)", message.strip(), re.IGNORECASE)
    if about_match:
        y_column = resolve_column(about_match.group(1), schema, preferred_type="number")
        if y_column:
            x_column = (
                resolve_column(context.last_x_column or "", schema, preferred_type="string")
                if context.last_x_column
                else resolve_first_by_types(schema, {"string", "categorical", "boolean"})
            )
            if x_column:
                return _grouped_plan(x_column, y_column, "Follow-up changed the metric and reused grouping context.")

    return base_plan


def _has_explicit_metric_and_group(message: str, schema: list[dict[str, Any]]) -> bool:
    by_match = re.search(r"\bby\s+([a-zA-Z0-9_ -]+)", message, flags=re.IGNORECASE)
    if not by_match:
        return False
    before_by = message[: by_match.start()]
    x_column = resolve_column(by_match.group(1), schema, preferred_type="string")
    y_column = _resolve_explicit_metric(before_by, schema)
    return x_column is not None and y_column is not None


def _resolve_explicit_metric(message: str, schema: list[dict[str, Any]]) -> str | None:
    for token in re.findall(r"[a-zA-Z0-9_]+", message):
        matched = resolve_column(token, schema)
        if matched:
            return matched
    return None


def _grouped_plan(x_column: str, y_column: str, explanation: str) -> AnalysisPlan:
    return AnalysisPlan(
        intent=AnalysisIntent.grouped_metric,
        title="Grouped Metric",
        requested_columns=[x_column, y_column],
        artifact_builders=[
            "build_grouped_metric_table",
            "build_grouped_metric_chart",
            "build_markdown_summary_artifact",
        ],
        x_column=x_column,
        y_column=y_column,
        explanation=explanation,
    )


def _trend_plan(x_column: str, y_column: str, explanation: str) -> AnalysisPlan:
    return AnalysisPlan(
        intent=AnalysisIntent.trend_over_time,
        title="Trend Over Time",
        requested_columns=[x_column, y_column],
        artifact_builders=[
            "build_trend_table",
            "build_trend_chart",
            "build_markdown_summary_artifact",
        ],
        x_column=x_column,
        y_column=y_column,
        explanation=explanation,
    )
