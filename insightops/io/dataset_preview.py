from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import math
import shutil

import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_float_dtype,
    is_integer_dtype,
    is_numeric_dtype,
)

from insightops.api.contracts import DatasetPreview, DatasetPreviewColumn

SUPPORTED_CSV_MIME_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "text/plain",
}
PREVIEW_ROW_LIMIT = 50
SAMPLE_VALUE_LIMIT = 5


def is_supported_csv_upload(filename: str, content_type: str | None) -> bool:
    if not filename.casefold().endswith(".csv"):
        return False
    if content_type is None:
        return True
    return content_type.casefold() in SUPPORTED_CSV_MIME_TYPES


def build_dataset_preview(
    source_path: Path,
    *,
    original_filename: str,
    size_bytes: int,
    storage_dir: Path,
) -> DatasetPreview:
    dataset_id = uuid4().hex
    storage_dir.mkdir(parents=True, exist_ok=True)
    stored_path = storage_dir / f"{dataset_id}.csv"
    shutil.copyfile(source_path, stored_path)

    dataframe = pd.read_csv(stored_path)
    preview_frame = dataframe.head(PREVIEW_ROW_LIMIT)

    return DatasetPreview(
        id=dataset_id,
        fileName=original_filename,
        mimeType="text/csv",
        sizeBytes=size_bytes,
        rowCount=int(len(dataframe)),
        previewRowCount=int(len(preview_frame)),
        columnCount=int(len(dataframe.columns)),
        columns=_column_previews(dataframe),
        previewRows=_clean_records(preview_frame),
    )


def _column_previews(dataframe: pd.DataFrame) -> list[DatasetPreviewColumn]:
    columns: list[DatasetPreviewColumn] = []
    for column_name in dataframe.columns:
        series = dataframe[column_name]
        columns.append(
            DatasetPreviewColumn(
                key=str(column_name),
                label=str(column_name),
                dataType=_infer_data_type(series),
                nullable=bool(series.isna().any()),
                sampleValues=_sample_values(series),
            )
        )
    return columns


def _infer_data_type(series: pd.Series) -> str:
    non_null = series.dropna()
    if non_null.empty:
        return "unknown"

    if is_bool_dtype(series):
        return "boolean"
    if is_integer_dtype(series):
        return "integer"
    if is_float_dtype(series):
        return "number"
    if is_numeric_dtype(series):
        return "number"
    if is_datetime64_any_dtype(series):
        return _datetime_type(series)

    as_text = non_null.astype(str).str.strip()
    date_like = as_text.str.match(r"^\d{4}-\d{2}-\d{2}([T\s]\d{2}:\d{2}(:\d{2})?)?$")
    if not bool(date_like.all()):
        return "string"

    parsed = pd.to_datetime(non_null, errors="coerce")
    if bool(parsed.notna().all()):
        return _datetime_type(parsed)

    return "string"


def _datetime_type(series: pd.Series) -> str:
    parsed = pd.to_datetime(series.dropna(), errors="coerce")
    if parsed.empty:
        return "datetime"
    if bool((parsed.dt.time == pd.Timestamp("00:00:00").time()).all()):
        return "date"
    return "datetime"


def _sample_values(series: pd.Series) -> list[object | None]:
    values: list[object | None] = []
    for value in series:
        cleaned = _clean_value(value)
        if cleaned is None or cleaned in values:
            continue
        values.append(cleaned)
        if len(values) == SAMPLE_VALUE_LIMIT:
            break
    return values


def _clean_records(dataframe: pd.DataFrame) -> list[dict[str, object | None]]:
    return [
        {str(key): _clean_value(value) for key, value in record.items()}
        for record in dataframe.to_dict(orient="records")
    ]


def _clean_value(value: object) -> object | None:
    if value is None:
        return None
    if pd.isna(value):
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.isoformat()
    if hasattr(value, "item"):
        return _clean_value(value.item())
    return value
