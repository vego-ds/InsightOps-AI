from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RunContext:
    run_id: str
    dataset_id: str
    message: str
    schema: list[Any]
    preview_rows: list[Any]
