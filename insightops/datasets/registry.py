from pathlib import Path
from threading import RLock

from insightops.datasets.models import DatasetMetadata
from insightops.datasets.storage import (
    delete_dataset_file,
    dataset_file_is_expired,
    validate_dataset_path_inside_root,
)


class DatasetRegistry:
    def __init__(self) -> None:
        self._datasets: dict[str, DatasetMetadata] = {}
        self._lock = RLock()

    def register(self, dataset: DatasetMetadata) -> None:
        with self._lock:
            self._datasets[dataset.dataset_id] = dataset

    def get(self, dataset_id: str) -> DatasetMetadata | None:
        with self._lock:
            return self._datasets.get(dataset_id)

    def get_path(self, dataset_id: str) -> Path | None:
        with self._lock:
            dataset = self._datasets.get(dataset_id)
            if dataset is None:
                return None

            storage_root = dataset.storage_root.resolve()
            dataset_path = dataset.path.resolve()
            if not dataset_path.is_relative_to(storage_root):
                return None
            return dataset_path

    def unregister(self, dataset_id: str) -> DatasetMetadata | None:
        with self._lock:
            return self._datasets.pop(dataset_id, None)

    def delete_registered(self, dataset_id: str) -> DatasetMetadata | None:
        with self._lock:
            dataset = self._datasets.get(dataset_id)
            if dataset is None:
                return None

            safe_path = validate_dataset_path_inside_root(
                dataset.path,
                storage_root=dataset.storage_root,
            )
            delete_dataset_file(safe_path, storage_root=dataset.storage_root)
            return self._datasets.pop(dataset_id, None)

    def cleanup_older_than(self, max_age_seconds: int) -> list[DatasetMetadata]:
        removed: list[DatasetMetadata] = []
        with self._lock:
            for dataset_id, dataset in list(self._datasets.items()):
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
                removed_dataset = self._datasets.pop(dataset_id, None)
                if removed_dataset is not None:
                    removed.append(removed_dataset)
        return removed

    def clear(self) -> None:
        with self._lock:
            self._datasets.clear()


_REGISTRY = DatasetRegistry()


def register_dataset(dataset: DatasetMetadata) -> None:
    _REGISTRY.register(dataset)


def get_dataset(dataset_id: str) -> DatasetMetadata | None:
    return _REGISTRY.get(dataset_id)


def get_dataset_path(dataset_id: str) -> Path | None:
    return _REGISTRY.get_path(dataset_id)


def unregister_dataset(dataset_id: str) -> DatasetMetadata | None:
    return _REGISTRY.unregister(dataset_id)


def delete_registered_dataset(dataset_id: str) -> DatasetMetadata | None:
    return _REGISTRY.delete_registered(dataset_id)


def cleanup_datasets_older_than(max_age_seconds: int) -> list[DatasetMetadata]:
    return _REGISTRY.cleanup_older_than(max_age_seconds)


def clear_dataset_registry() -> None:
    _REGISTRY.clear()
