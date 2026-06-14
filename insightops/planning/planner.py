import re
from typing import Any

from insightops.planning.column_resolver import resolve_column, resolve_first_by_types
from insightops.planning.intents import AnalysisIntent, AnalysisPlan

Schema = list[dict[str, Any]]

BY_PATTERN = re.compile(r"\bby\s+([a-zA-Z0-9_ -]+)", flags=re.IGNORECASE)
TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")

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
