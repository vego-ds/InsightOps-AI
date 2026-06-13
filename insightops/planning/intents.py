from enum import StrEnum

from pydantic import BaseModel


class AnalysisIntent(StrEnum):
    dataset_summary = "dataset_summary"
    missing_values = "missing_values"
    numeric_summary = "numeric_summary"
    grouped_metric = "grouped_metric"
    top_categories = "top_categories"
    trend_over_time = "trend_over_time"
    unknown = "unknown"


class AnalysisPlan(BaseModel):
    intent: AnalysisIntent
    title: str
    requested_columns: list[str]
    artifact_builders: list[str]
    x_column: str | None = None
    y_column: str | None = None
    explanation: str
