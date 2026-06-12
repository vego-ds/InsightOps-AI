from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DatasetMetadata:
    dataset_id: str
    file_name: str
    mime_type: str
    size_bytes: int
    path: Path
    storage_root: Path
