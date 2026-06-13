from pathlib import Path

from insightops.datasets.models import DatasetMetadata
from insightops.datasets.storage import (
    delete_dataset_file,
    dataset_file_is_expired,
    validate_dataset_path_inside_root,
)

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


def unregister_dataset(dataset_id: str) -> DatasetMetadata | None:
    return _DATASETS.pop(dataset_id, None)


def delete_registered_dataset(dataset_id: str) -> DatasetMetadata | None:
    dataset = get_dataset(dataset_id)
    if dataset is None:
        return None

    safe_path = validate_dataset_path_inside_root(
        dataset.path,
        storage_root=dataset.storage_root,
    )
    delete_dataset_file(safe_path, storage_root=dataset.storage_root)
    return unregister_dataset(dataset_id)


def cleanup_datasets_older_than(max_age_seconds: int) -> list[DatasetMetadata]:
    removed: list[DatasetMetadata] = []
    for dataset_id, dataset in list(_DATASETS.items()):
        safe_path = validate_dataset_path_inside_root(
            dataset.path,
            storage_root=dataset.storage_root,
        )
        if not dataset_file_is_expired(
            safe_path,
            max_age_seconds=max_age_seconds,
        ):
            continue

        delete_dataset_file(safe_path, storage_root=dataset.storage_root)
        removed_dataset = unregister_dataset(dataset_id)
        if removed_dataset is not None:
            removed.append(removed_dataset)
    return removed


def clear_dataset_registry() -> None:
    _DATASETS.clear()
