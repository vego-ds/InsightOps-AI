from dataclasses import dataclass
from pathlib import Path
from typing import Any

from insightops.datasets.models import DatasetMetadata


@dataclass(frozen=True)
class RunContext:
    run_id: str
    dataset_id: str
    message: str
    schema: list[Any]
    preview_rows: list[Any]
    dataset_metadata: DatasetMetadata | None = None
    dataset_path: Path | None = None
