import math
import re
from typing import Any

from insightops.artifacts.models import (
    CHART_TYPE_VALUES,
    MAX_CHART_ROWS,
    MAX_TABLE_ROWS,
    TABLE_COLUMN_TYPE_VALUES,
    ArtifactScalar,
)

HTML_TAG_RE = re.compile(r"<[^>]+>")


def validate_table_artifact(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("kind") != "table":
        raise ValueError("Artifact kind must be table.")
    columns = payload.get("columns")
    rows = payload.get("rows")
    if not isinstance(columns, list) or not columns:
        raise ValueError("Table artifact columns must be a non-empty list.")
    if not isinstance(rows, list):
        raise ValueError("Table artifact rows must be a list.")

    safe_columns = [_validate_table_column(column) for column in columns]
    column_keys = [column["key"] for column in safe_columns]
    safe_rows: list[dict[str, ArtifactScalar]] = []
    for row in rows[:MAX_TABLE_ROWS]:
        if not isinstance(row, dict):
            raise ValueError("Table artifact rows must be flat records.")
        safe_rows.append({key: sanitize_scalar(row.get(key)) for key in column_keys})

    return {
        "id": _required_text(payload, "id"),
        "kind": "table",
        "title": _required_text(payload, "title"),
        "columns": safe_columns,
        "rows": safe_rows,
    }


def validate_chart_artifact(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("kind") != "chart":
        raise ValueError("Artifact kind must be chart.")
    chart_type = payload.get("chartType")
    if chart_type not in CHART_TYPE_VALUES:
        raise ValueError("Invalid chart type.")
    x_key = _required_text(payload, "xKey")
    y_key = _required_text(payload, "yKey")
    data = payload.get("data")
    if not isinstance(data, list):
        raise ValueError("Chart artifact data must be a list.")

    safe_data: list[dict[str, str | int | float]] = []
    for row in data[:MAX_CHART_ROWS]:
        if not isinstance(row, dict):
            raise ValueError("Chart artifact rows must be flat records.")
        x_value = sanitize_scalar(row.get(x_key))
        y_value = sanitize_scalar(row.get(y_key))
        if not isinstance(x_value, str | int | float) or isinstance(x_value, bool):
            raise ValueError("Chart x values must be string or numeric.")
        if not isinstance(y_value, int | float) or isinstance(y_value, bool):
            raise ValueError("Chart y values must be numeric.")
        safe_data.append({x_key: x_value, y_key: y_value})

    return {
        "id": _required_text(payload, "id"),
        "kind": "chart",
        "title": _required_text(payload, "title"),
        "chartType": chart_type,
        "xKey": x_key,
        "yKey": y_key,
        "data": safe_data,
    }


def validate_markdown_artifact(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("kind") != "markdown":
        raise ValueError("Artifact kind must be markdown.")
    text = _required_text(payload, "text")
    if HTML_TAG_RE.search(text):
        text = HTML_TAG_RE.sub("", text)
    return {
        "id": _required_text(payload, "id"),
        "kind": "markdown",
        "title": _required_text(payload, "title"),
        "text": text,
    }


def sanitize_scalar(value: Any) -> ArtifactScalar:
    if value is None:
        return None
    if isinstance(value, bool | str | int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    raise ValueError("Artifact values must be flat scalar values.")


def _validate_table_column(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError("Table columns must be column descriptor records.")
    key = _required_text(value, "key")
    label = _required_text(value, "label")
    data_type = _required_text(value, "dataType")
    if data_type not in TABLE_COLUMN_TYPE_VALUES:
        raise ValueError("Invalid table column dataType.")
    return {"key": key, "label": label, "dataType": data_type}


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string.")
    return value
