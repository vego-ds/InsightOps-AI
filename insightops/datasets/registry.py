from pathlib import Path

from insightops.datasets.models import DatasetMetadata

_DATASETS: dict[str, DatasetMetadata] = {}


def register_dataset(dataset: DatasetMetadata) -> None:
    _DATASETS[dataset.dataset_id] = dataset


def get_dataset(dataset_id: str) -> DatasetMetadata | None:
    return _DATASETS.get(dataset_id)


def get_dataset_path(dataset_id: str) -> Path | None:
    dataset = get_dataset(dataset_id)
    if dataset is None:
        return None

    storage_root = dataset.storage_root.resolve()
    dataset_path = dataset.path.resolve()
    if not dataset_path.is_relative_to(storage_root):
        return None
    return dataset_path


def clear_dataset_registry() -> None:
    _DATASETS.clear()
