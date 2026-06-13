from collections import defaultdict
import csv
from pathlib import Path
from statistics import mean

from insightops.artifacts.models import MAX_CHART_ROWS, MAX_TABLE_ROWS
from insightops.artifacts.validators import (
    sanitize_scalar,
    validate_chart_artifact,
    validate_markdown_artifact,
    validate_table_artifact,
)
from insightops.runtime.run_context import RunContext


def build_dataset_profile_table(context: RunContext) -> dict:
    rows, columns = _read_csv(context)
    numeric_columns = _numeric_columns(rows, columns)
    categorical_columns = _categorical_columns(rows, columns, numeric_columns)
    return validate_table_artifact(
        {
            "id": f"{context.run_id}-dataset-profile",
            "kind": "table",
            "title": "Dataset Profile",
            "columns": [
                _column("metric", "Metric", "string"),
                _column("value", "Value", "string"),
            ],
            "rows": [
                {"metric": "Rows", "value": len(rows)},
                {"metric": "Columns", "value": len(columns)},
                {"metric": "Numeric columns", "value": len(numeric_columns)},
                {"metric": "Categorical columns", "value": len(categorical_columns)},
            ],
        }
    )


def build_missing_values_table(context: RunContext) -> dict:
    rows, columns = _read_csv(context)
    total_rows = len(rows)
    missing_rows = []
    for name in columns[:MAX_TABLE_ROWS]:
        missing_count = sum(1 for row in rows if _is_missing(row.get(name, "")))
        missing_rows.append(
            {
                "column": name,
                "missingCount": missing_count,
                "missingRate": round(missing_count / total_rows, 4) if total_rows else 0,
            }
        )
    return validate_table_artifact(
        {
            "id": f"{context.run_id}-missing-values",
            "kind": "table",
            "title": "Missing Values",
            "columns": [
                _column("column", "Column", "string"),
                _column("missingCount", "Missing Count", "integer"),
                _column("missingRate", "Missing Rate", "number"),
            ],
            "rows": missing_rows,
        }
    )


def build_numeric_summary_table(context: RunContext) -> dict:
    rows, columns = _read_csv(context)
    summary_rows = []
    for name in _numeric_columns(rows, columns)[:MAX_TABLE_ROWS]:
        values = [_parse_number(row.get(name, "")) for row in rows]
        numeric_values = [value for value in values if value is not None]
        if not numeric_values:
            continue
        summary_rows.append(
            {
                "column": name,
                "count": len(numeric_values),
                "mean": round(mean(numeric_values), 4),
                "min": min(numeric_values),
                "max": max(numeric_values),
            }
        )
    return validate_table_artifact(
        {
            "id": f"{context.run_id}-numeric-summary",
            "kind": "table",
            "title": "Numeric Summary",
            "columns": [
                _column("column", "Column", "string"),
                _column("count", "Count", "integer"),
                _column("mean", "Mean", "number"),
                _column("min", "Min", "number"),
                _column("max", "Max", "number"),
            ],
            "rows": summary_rows,
        }
    )


def build_basic_chart_artifact(context: RunContext) -> dict | None:
    rows, columns = _read_csv(context)
    numeric_columns = _numeric_columns(rows, columns)
    categorical_columns = _categorical_columns(rows, columns, numeric_columns)
    if not rows or not numeric_columns or not categorical_columns:
        return None

    x_key = categorical_columns[0]
    y_source = numeric_columns[0]
    y_key = f"sum_{y_source}"
    aggregates: dict[str, float] = defaultdict(float)
    for row in rows:
        category = row.get(x_key, "").strip() or "Unknown"
        number = _parse_number(row.get(y_source, ""))
        if number is not None:
            aggregates[category] += number

    data = [
        {x_key: category, y_key: round(value, 4)}
        for category, value in sorted(
            aggregates.items(),
            key=lambda item: (-item[1], item[0]),
        )[:MAX_CHART_ROWS]
    ]
    if not data:
        return None

    return validate_chart_artifact(
        {
            "id": f"{context.run_id}-basic-chart",
            "kind": "chart",
            "title": f"{y_source} by {x_key}",
            "chartType": "bar",
            "xKey": x_key,
            "yKey": y_key,
            "data": data,
        }
    )


def build_markdown_summary_artifact(context: RunContext) -> dict:
    rows, columns = _read_csv(context)
    numeric_columns = _numeric_columns(rows, columns)
    categorical_columns = _categorical_columns(rows, columns, numeric_columns)
    missing_columns = [
        name for name in columns if any(_is_missing(row.get(name, "")) for row in rows)
    ]
    missing_note = (
        f"Missing values detected in {len(missing_columns)} column(s): "
        + ", ".join(missing_columns[:8])
        if missing_columns
        else "No missing values detected in the parsed CSV rows."
    )
    return validate_markdown_artifact(
        {
            "id": f"{context.run_id}-markdown-summary",
            "kind": "markdown",
            "title": "Dataset Summary",
            "text": (
                f"Rows: {len(rows)}\n"
                f"Columns: {len(columns)}\n"
                f"Likely numeric columns: {_join_or_none(numeric_columns)}\n"
                f"Likely categorical columns: {_join_or_none(categorical_columns)}\n"
                f"{missing_note}"
            ),
        }
    )


def build_all_artifacts(context: RunContext) -> list[dict]:
    artifacts = [
        build_dataset_profile_table(context),
        build_missing_values_table(context),
        build_numeric_summary_table(context),
    ]
    chart = build_basic_chart_artifact(context)
    if chart is not None:
        artifacts.append(chart)
    artifacts.append(build_markdown_summary_artifact(context))
    return artifacts


def get_dataset_shape(context: RunContext) -> tuple[int, int]:
    rows, columns = _read_csv(context)
    return len(rows), len(columns)


def build_artifacts_for_plan(context: RunContext, plan) -> list[dict]:
    artifacts = []
    for builder_name in plan.artifact_builders:
        artifact = _build_named_artifact(context, plan, builder_name)
        if artifact is None:
            continue
        if isinstance(artifact, list):
            artifacts.extend(artifact)
        else:
            artifacts.append(artifact)
    return artifacts or [build_dataset_profile_table(context), build_markdown_summary_artifact(context)]


def build_grouped_metric_table(
    context: RunContext,
    x_column: str | None = None,
    y_column: str | None = None,
) -> dict | None:
    rows, columns = _read_csv(context)
    x_column, y_column = _resolve_xy(rows, columns, x_column, y_column)
    if x_column is None or y_column is None:
        return None
    grouped = _group_sum(rows, x_column, y_column)
    return validate_table_artifact(
        {
            "id": f"{context.run_id}-grouped-metric",
            "kind": "table",
            "title": f"{y_column} by {x_column}",
            "columns": [
                _column(x_column, x_column, "string"),
                _column(f"sum_{y_column}", f"Sum {y_column}", "number"),
            ],
            "rows": [
                {x_column: key, f"sum_{y_column}": round(value, 4)}
                for key, value in grouped[:MAX_TABLE_ROWS]
            ],
        }
    )


def build_grouped_metric_chart(
    context: RunContext,
    x_column: str | None = None,
    y_column: str | None = None,
) -> dict | None:
    rows, columns = _read_csv(context)
    x_column, y_column = _resolve_xy(rows, columns, x_column, y_column)
    if x_column is None or y_column is None:
        return None
    y_key = f"sum_{y_column}"
    return validate_chart_artifact(
        {
            "id": f"{context.run_id}-grouped-chart",
            "kind": "chart",
            "title": f"{y_column} by {x_column}",
            "chartType": "bar",
            "xKey": x_column,
            "yKey": y_key,
            "data": [
                {x_column: key, y_key: round(value, 4)}
                for key, value in _group_sum(rows, x_column, y_column)[:MAX_CHART_ROWS]
            ],
        }
    )


def build_top_categories_table(
    context: RunContext,
    x_column: str | None = None,
    y_column: str | None = None,
) -> dict | None:
    return build_grouped_metric_table(context, x_column, y_column)


def build_trend_table(
    context: RunContext,
    x_column: str | None = None,
    y_column: str | None = None,
) -> dict | None:
    rows, columns = _read_csv(context)
    x_column, y_column = _resolve_xy(rows, columns, x_column, y_column)
    if x_column is None or y_column is None:
        return None
    grouped = sorted(_group_sum(rows, x_column, y_column), key=lambda item: item[0])
    return validate_table_artifact(
        {
            "id": f"{context.run_id}-trend-table",
            "kind": "table",
            "title": f"{y_column} over {x_column}",
            "columns": [
                _column(x_column, x_column, "string"),
                _column(f"sum_{y_column}", f"Sum {y_column}", "number"),
            ],
            "rows": [
                {x_column: key, f"sum_{y_column}": round(value, 4)}
                for key, value in grouped[:MAX_TABLE_ROWS]
            ],
        }
    )


def build_trend_chart(
    context: RunContext,
    x_column: str | None = None,
    y_column: str | None = None,
) -> dict | None:
    rows, columns = _read_csv(context)
    x_column, y_column = _resolve_xy(rows, columns, x_column, y_column)
    if x_column is None or y_column is None:
        return None
    y_key = f"sum_{y_column}"
    grouped = sorted(_group_sum(rows, x_column, y_column), key=lambda item: item[0])
    return validate_chart_artifact(
        {
            "id": f"{context.run_id}-trend-chart",
            "kind": "chart",
            "title": f"{y_column} over {x_column}",
            "chartType": "line",
            "xKey": x_column,
            "yKey": y_key,
            "data": [
                {x_column: key, y_key: round(value, 4)}
                for key, value in grouped[:MAX_CHART_ROWS]
            ],
        }
    )


def _build_named_artifact(context: RunContext, plan, builder_name: str):
    if builder_name == "build_dataset_profile_table":
        return build_dataset_profile_table(context)
    if builder_name == "build_missing_values_table":
        return build_missing_values_table(context)
    if builder_name == "build_numeric_summary_table":
        return build_numeric_summary_table(context)
    if builder_name == "build_basic_chart_artifact":
        return build_basic_chart_artifact(context)
    if builder_name == "build_markdown_summary_artifact":
        return build_markdown_summary_artifact(context)
    if builder_name == "build_grouped_metric_table":
        return build_grouped_metric_table(context, plan.x_column, plan.y_column)
    if builder_name == "build_grouped_metric_chart":
        return build_grouped_metric_chart(context, plan.x_column, plan.y_column)
    if builder_name == "build_top_categories_table":
        return build_top_categories_table(context, plan.x_column, plan.y_column)
    if builder_name == "build_trend_table":
        return build_trend_table(context, plan.x_column, plan.y_column)
    if builder_name == "build_trend_chart":
        return build_trend_chart(context, plan.x_column, plan.y_column)
    return None


def _read_csv(context: RunContext) -> tuple[list[dict[str, str]], list[str]]:
    if context.dataset_path is None:
        raise ValueError("RunContext is missing dataset_path.")
    return _read_csv_path(context.dataset_path)


def _read_csv_path(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = [str(name) for name in (reader.fieldnames or [])]
        rows = [
            {column: str(row.get(column) or "") for column in columns}
            for row in reader
        ]
    return rows, columns


def _numeric_columns(rows: list[dict[str, str]], columns: list[str]) -> list[str]:
    numeric = []
    for name in columns:
        present_values = [row.get(name, "") for row in rows if not _is_missing(row.get(name, ""))]
        if present_values and all(_parse_number(value) is not None for value in present_values):
            numeric.append(name)
    return numeric


def _categorical_columns(
    rows: list[dict[str, str]],
    columns: list[str],
    numeric_columns: list[str],
) -> list[str]:
    numeric = set(numeric_columns)
    categorical = []
    for name in columns:
        if name in numeric:
            continue
        distinct = {row.get(name, "").strip() for row in rows if not _is_missing(row.get(name, ""))}
        if distinct:
            categorical.append(name)
    return categorical


def _parse_number(value: str | None) -> float | None:
    if value is None or _is_missing(value):
        return None
    try:
        return_value = float(value)
    except ValueError:
        return None
    try:
        sanitized = sanitize_scalar(return_value)
    except ValueError:
        return None
    return sanitized if isinstance(sanitized, float | int) and not isinstance(sanitized, bool) else None


def _is_missing(value: str | None) -> bool:
    return value is None or value.strip() == ""


def _column(key: str, label: str, data_type: str) -> dict[str, str]:
    return {"key": key, "label": label, "dataType": data_type}


def _join_or_none(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


def _resolve_xy(
    rows: list[dict[str, str]],
    columns: list[str],
    x_column: str | None,
    y_column: str | None,
) -> tuple[str | None, str | None]:
    numeric_columns = _numeric_columns(rows, columns)
    categorical_columns = _categorical_columns(rows, columns, numeric_columns)
    resolved_x = x_column if x_column in columns else (categorical_columns[0] if categorical_columns else None)
    resolved_y = y_column if y_column in numeric_columns else (numeric_columns[0] if numeric_columns else None)
    return resolved_x, resolved_y


def _group_sum(
    rows: list[dict[str, str]],
    x_column: str,
    y_column: str,
) -> list[tuple[str, float]]:
    grouped: dict[str, float] = defaultdict(float)
    for row in rows:
        key = row.get(x_column, "").strip() or "Unknown"
        value = _parse_number(row.get(y_column, ""))
        if value is not None:
            grouped[key] += value
    return sorted(grouped.items(), key=lambda item: (-item[1], item[0]))
