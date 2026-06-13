import re
from typing import Any

from insightops.planning.column_resolver import resolve_column, resolve_first_by_types
from insightops.planning.intents import AnalysisIntent, AnalysisPlan


def build_analysis_plan(message: str, schema: list[dict[str, Any]]) -> AnalysisPlan:
    prompt = message.casefold()
    if _contains(prompt, {"missing", "null", "empty", "blanks"}):
        return AnalysisPlan(
            intent=AnalysisIntent.missing_values,
            title="Missing Values",
            requested_columns=[],
            artifact_builders=["build_missing_values_table", "build_markdown_summary_artifact"],
            explanation="Prompt requested missing, null, empty, or blank value analysis.",
        )
    if _contains(prompt, {"trend", "time", "date", "monthly", "daily"}):
        y_column = _resolve_metric_from_prompt(message, schema)
        x_column = resolve_column("date", schema, preferred_type="date") or resolve_first_by_types(
            schema, {"date", "datetime"}
        )
        return AnalysisPlan(
            intent=AnalysisIntent.trend_over_time,
            title="Trend Over Time",
            requested_columns=[column for column in [x_column, y_column] if column],
            artifact_builders=["build_trend_table", "build_trend_chart", "build_markdown_summary_artifact"],
            x_column=x_column,
            y_column=y_column,
            explanation="Prompt requested time, date, daily, monthly, or trend analysis.",
        )
    by_match = re.search(r"\bby\s+([a-zA-Z0-9_ -]+)", message, flags=re.IGNORECASE)
    if by_match:
        x_column = resolve_column(by_match.group(1), schema, preferred_type="string")
        y_column = _resolve_metric_from_prompt(message[: by_match.start()], schema)
        return AnalysisPlan(
            intent=AnalysisIntent.grouped_metric,
            title="Grouped Metric",
            requested_columns=[column for column in [x_column, y_column] if column],
            artifact_builders=[
                "build_grouped_metric_table",
                "build_grouped_metric_chart",
                "build_markdown_summary_artifact",
            ],
            x_column=x_column,
            y_column=y_column,
            explanation='Prompt matched a deterministic "by <column>" grouping pattern.',
        )
    if _contains(prompt, {"top", "best", "highest", "most"}):
        x_column = _resolve_category_from_prompt(message, schema)
        y_column = _resolve_metric_from_prompt(message, schema)
        return AnalysisPlan(
            intent=AnalysisIntent.top_categories,
            title="Top Categories",
            requested_columns=[column for column in [x_column, y_column] if column],
            artifact_builders=[
                "build_top_categories_table",
                "build_grouped_metric_chart",
                "build_markdown_summary_artifact",
            ],
            x_column=x_column,
            y_column=y_column,
            explanation="Prompt requested top, best, highest, or most categories.",
        )
    if _contains(prompt, {"numeric", "statistics", "mean", "average", "min", "max"}):
        return AnalysisPlan(
            intent=AnalysisIntent.numeric_summary,
            title="Numeric Summary",
            requested_columns=[],
            artifact_builders=["build_numeric_summary_table", "build_markdown_summary_artifact"],
            explanation="Prompt requested numeric statistics.",
        )
    if _contains(prompt, {"summary", "overview", "profile"}):
        return _dataset_summary_plan("Prompt requested summary, overview, or profile.")
    return _dataset_summary_plan("Prompt did not match a specific intent; using safe dataset summary.")


def _dataset_summary_plan(explanation: str) -> AnalysisPlan:
    return AnalysisPlan(
        intent=AnalysisIntent.dataset_summary,
        title="Dataset Summary",
        requested_columns=[],
        artifact_builders=[
            "build_dataset_profile_table",
            "build_basic_chart_artifact",
            "build_markdown_summary_artifact",
        ],
        explanation=explanation,
    )


def _resolve_metric_from_prompt(message: str, schema: list[dict[str, Any]]) -> str | None:
    for token in re.findall(r"[a-zA-Z0-9_]+", message):
        matched = resolve_column(token, schema)
        if matched:
            return matched
    return resolve_column("sales", schema, preferred_type="number") or resolve_first_by_types(
        schema, {"number", "integer"}
    )


def _resolve_category_from_prompt(message: str, schema: list[dict[str, Any]]) -> str | None:
    for token in re.findall(r"[a-zA-Z0-9_]+", message):
        matched = resolve_column(token, schema)
        if matched:
            return matched
    return resolve_first_by_types(schema, {"string", "categorical", "boolean"})


def _contains(prompt: str, keywords: set[str]) -> bool:
    return any(keyword in prompt for keyword in keywords)
