from pathlib import Path

from pydantic import BaseModel


class DatasetSourceMetadata(BaseModel):
    source_type: str
    file_name: str
    file_size_bytes: int
    collection_method: str
    record_count: int
    notes: str = ""


def create_sample_source_metadata(
    path: str,
    record_count: int,
) -> DatasetSourceMetadata:
    csv_path = Path(path)
    return DatasetSourceMetadata(
        source_type="sample_csv",
        file_name=_safe_file_name(csv_path.name),
        file_size_bytes=csv_path.stat().st_size if csv_path.exists() else 0,
        collection_method="bundled_sample_file",
        record_count=record_count,
        notes="Bundled deterministic sample sales dataset.",
    )


def create_uploaded_source_metadata(
    file_name: str,
    file_size_bytes: int,
    record_count: int,
) -> DatasetSourceMetadata:
    return DatasetSourceMetadata(
        source_type="uploaded_csv",
        file_name=_safe_file_name(file_name),
        file_size_bytes=file_size_bytes,
        collection_method="api_upload",
        record_count=record_count,
        notes="User-provided CSV uploaded through the analysis API.",
    )


def _safe_file_name(file_name: str) -> str:
    safe_name = Path(file_name).name.strip()
    return safe_name or "unknown.csv"
