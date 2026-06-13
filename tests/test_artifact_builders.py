import math
from pathlib import Path

import pytest

from insightops.artifacts.builders import (
    build_basic_chart_artifact,
    build_grouped_metric_chart,
    build_grouped_metric_table,
    build_dataset_profile_table,
    build_markdown_summary_artifact,
    build_missing_values_table,
    build_numeric_summary_table,
    build_trend_chart,
)
from insightops.artifacts.models import MAX_CHART_ROWS, MAX_TABLE_ROWS
from insightops.artifacts.validators import (
    sanitize_scalar,
    validate_chart_artifact,
    validate_table_artifact,
)
from insightops.datasets import DatasetMetadata
from insightops.runtime import RunContext


def test_dataset_profile_table_artifact_validates(tmp_path: Path) -> None:
    artifact = build_dataset_profile_table(_context(tmp_path))

    assert artifact["kind"] == "table"
    assert artifact["columns"][0] == {
        "key": "metric",
        "label": "Metric",
        "dataType": "string",
    }
    assert artifact["rows"]


def test_missing_values_table_artifact_validates(tmp_path: Path) -> None:
    artifact = build_missing_values_table(_context(tmp_path))

    assert artifact["kind"] == "table"
    assert any(row["missingCount"] > 0 for row in artifact["rows"])


def test_numeric_summary_table_artifact_validates(tmp_path: Path) -> None:
    artifact = build_numeric_summary_table(_context(tmp_path))

    assert artifact["kind"] == "table"
    assert artifact["rows"][0]["column"] == "revenue"
    assert artifact["rows"][0]["count"] == 3


def test_chart_artifact_validates(tmp_path: Path) -> None:
    artifact = build_basic_chart_artifact(_context(tmp_path))

    assert artifact is not None
    assert artifact["kind"] == "chart"
    assert artifact["chartType"] == "bar"
    assert artifact["xKey"] == "region"
    assert artifact["yKey"] == "sum_revenue"


def test_markdown_artifact_validates(tmp_path: Path) -> None:
    artifact = build_markdown_summary_artifact(_context(tmp_path))

    assert artifact["kind"] == "markdown"
    assert "Rows: 4" in artifact["text"]
    assert "<" not in artifact["text"]


def test_grouped_metric_table_validates(tmp_path: Path) -> None:
    artifact = build_grouped_metric_table(_context(tmp_path), "region", "revenue")

    assert artifact is not None
    assert artifact["kind"] == "table"
    assert artifact["rows"][0]["region"] == "North"


def test_grouped_metric_chart_validates(tmp_path: Path) -> None:
    artifact = build_grouped_metric_chart(_context(tmp_path), "region", "revenue")

    assert artifact is not None
    assert artifact["kind"] == "chart"
    assert artifact["xKey"] == "region"


def test_trend_chart_validates(tmp_path: Path) -> None:
    artifact = build_trend_chart(_context(tmp_path), "order_date", "revenue")

    assert artifact is not None
    assert artifact["kind"] == "chart"
    assert artifact["chartType"] == "line"


def test_nan_and_infinity_are_converted_or_rejected() -> None:
    assert sanitize_scalar(math.nan) is None
    assert sanitize_scalar(math.inf) is None


def test_nested_values_are_rejected() -> None:
    with pytest.raises(ValueError, match="flat scalar"):
        sanitize_scalar({"nested": True})


def test_table_row_count_is_bounded() -> None:
    artifact = validate_table_artifact(
        {
            "id": "table-1",
            "kind": "table",
            "title": "Bounded Table",
            "columns": [{"key": "value", "label": "Value", "dataType": "integer"}],
            "rows": [{"value": index} for index in range(MAX_TABLE_ROWS + 5)],
        }
    )

    assert len(artifact["rows"]) == MAX_TABLE_ROWS


def test_chart_row_count_is_bounded() -> None:
    artifact = validate_chart_artifact(
        {
            "id": "chart-1",
            "kind": "chart",
            "title": "Bounded Chart",
            "chartType": "bar",
            "xKey": "category",
            "yKey": "value",
            "data": [
                {"category": f"cat-{index}", "value": index}
                for index in range(MAX_CHART_ROWS + 5)
            ],
        }
    )

    assert len(artifact["data"]) == MAX_CHART_ROWS


def test_unknown_columns_fall_back_safely(tmp_path: Path) -> None:
    artifact = build_grouped_metric_chart(_context(tmp_path), "does_not_exist", "also_missing")

    assert artifact is not None
    assert artifact["xKey"] == "region"
    assert artifact["yKey"] == "sum_revenue"


def test_artifact_rows_are_bounded_and_scalar(tmp_path: Path) -> None:
    artifact = build_grouped_metric_table(_context(tmp_path), "region", "revenue")

    assert artifact is not None
    assert len(artifact["rows"]) <= MAX_TABLE_ROWS
    for row in artifact["rows"]:
        for value in row.values():
            assert isinstance(value, str | int | float | bool) or value is None


def _context(tmp_path: Path) -> RunContext:
    dataset_path = tmp_path / "sales.csv"
    dataset_path.write_text(
        "region,revenue,quantity,segment,order_date\n"
        "North,1200,2,Enterprise,2026-01-01\n"
        "South,800,1,SMB,2026-01-02\n"
        "North,300,3,,2026-01-03\n"
        "West,,4,SMB,2026-01-04\n",
        encoding="utf-8",
    )
    metadata = DatasetMetadata(
        dataset_id="dataset-123",
        file_name="sales.csv",
        mime_type="text/csv",
        size_bytes=dataset_path.stat().st_size,
        path=dataset_path,
        storage_root=tmp_path,
    )
    return RunContext(
        run_id="run-123",
        dataset_id=metadata.dataset_id,
        message="Summarize revenue.",
        schema=[],
        preview_rows=[],
        dataset_metadata=metadata,
        dataset_path=dataset_path,
    )
