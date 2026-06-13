from typing import Any

from insightops.datasets.models import DatasetMetadata
from insightops.planning.intents import AnalysisIntent, AnalysisPlan


def synthesize_final_answer(
    *,
    plan: AnalysisPlan,
    artifacts: list[dict[str, Any]],
    dataset_metadata: DatasetMetadata | None = None,
    row_count: int | None = None,
    column_count: int | None = None,
) -> str:
    artifact_types = _artifact_types(artifacts)
    dataset_name = dataset_metadata.file_name if dataset_metadata else "the dataset"
    shape = _shape_text(row_count=row_count, column_count=column_count)
    columns = _column_text(plan)
    artifact_text = _artifact_text(artifact_types)
    base = _intent_sentence(plan.intent, columns)
    return (
        f"{base} I generated {artifact_text} for {dataset_name}{shape}. "
        "The results are available in the Artifacts tab and focused in the Data Canvas."
    )


def _intent_sentence(intent: AnalysisIntent, columns: str) -> str:
    if intent == AnalysisIntent.dataset_summary:
        return "I ran a deterministic dataset summary/profile analysis."
    if intent == AnalysisIntent.missing_values:
        return "I ran a deterministic missing-values analysis."
    if intent == AnalysisIntent.numeric_summary:
        return "I ran a deterministic numeric summary analysis."
    if intent == AnalysisIntent.grouped_metric:
        return f"I ran a deterministic grouped metric analysis{columns}."
    if intent == AnalysisIntent.top_categories:
        return f"I ran a deterministic top categories ranking analysis{columns}."
    if intent == AnalysisIntent.trend_over_time:
        return f"I ran a deterministic time trend analysis{columns}."
    return "I ran a deterministic fallback analysis."


def _column_text(plan: AnalysisPlan) -> str:
    if plan.x_column and plan.y_column:
        return f" using {plan.y_column} by {plan.x_column}"
    if plan.y_column:
        return f" using {plan.y_column}"
    if plan.x_column:
        return f" using {plan.x_column}"
    return ""


def _artifact_types(artifacts: list[dict[str, Any]]) -> list[str]:
    ordered = []
    for kind in ("chart", "table", "markdown"):
        if any(artifact.get("kind") == kind for artifact in artifacts):
            ordered.append(kind)
    return ordered


def _artifact_text(artifact_types: list[str]) -> str:
    if not artifact_types:
        return "no artifacts"
    labels = {
        "chart": "chart artifact",
        "table": "table artifact",
        "markdown": "markdown summary artifact",
    }
    rendered = [labels.get(kind, f"{kind} artifact") for kind in artifact_types]
    if len(rendered) == 1:
        return rendered[0]
    return ", ".join(rendered[:-1]) + f", and {rendered[-1]}"


def _shape_text(row_count: int | None, column_count: int | None) -> str:
    if row_count is None and column_count is None:
        return ""
    if row_count is None:
        return f" with {column_count} columns"
    if column_count is None:
        return f" with {row_count} rows"
    return f" with {row_count} rows and {column_count} columns"
