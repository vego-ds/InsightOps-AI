from pathlib import Path
import os
import shutil
import tempfile
import time


DATASET_STORAGE_ROOT = Path("scratch/datasets")
COPY_BUFFER_SIZE = 1024 * 1024


class DatasetStorageError(RuntimeError):
    """Raised when dataset storage cannot complete a filesystem operation."""


def save_dataset_file(
    source_path: Path,
    *,
    dataset_id: str,
    storage_root: Path = DATASET_STORAGE_ROOT,
) -> Path:
    root = _ensure_storage_root(storage_root)
    stored_path = _dataset_path_for_id(dataset_id, storage_root=root)
    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=root,
            prefix=".dataset-",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            with source_path.open("rb") as source_file:
                shutil.copyfileobj(source_file, temp_file, length=COPY_BUFFER_SIZE)
            temp_file.flush()
            os.fsync(temp_file.fileno())

        os.replace(temp_path, stored_path)
        return stored_path
    except OSError as error:
        if temp_path is not None:
            _remove_temporary_file(temp_path)
        raise DatasetStorageError(
            f"Failed to persist dataset file '{source_path}' to controlled storage.",
        ) from error


def validate_dataset_path_inside_root(
    dataset_path: Path,
    *,
    storage_root: Path = DATASET_STORAGE_ROOT,
) -> Path:
    root = _resolved_storage_root(storage_root)
    resolved_path = dataset_path.resolve()
    if not resolved_path.is_relative_to(root):
        raise ValueError("Dataset path escaped controlled storage root.")
    return resolved_path


def delete_dataset_file(
    dataset_path: Path,
    *,
    storage_root: Path = DATASET_STORAGE_ROOT,
) -> None:
    safe_path = validate_dataset_path_inside_root(
        dataset_path,
        storage_root=storage_root,
    )
    try:
        safe_path.unlink(missing_ok=True)
    except OSError as error:
        raise DatasetStorageError(
            f"Failed to delete dataset file '{safe_path}' from controlled storage.",
        ) from error


def dataset_file_is_expired(
    dataset_path: Path,
    *,
    max_age_seconds: int,
    now_seconds: float | None = None,
) -> bool:
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds must be non-negative.")

    try:
        modified_time = dataset_path.stat().st_mtime
    except FileNotFoundError:
        return True
    except OSError as error:
        raise DatasetStorageError(
            f"Failed to inspect dataset file age for '{dataset_path}'.",
        ) from error

    now = time.time() if now_seconds is None else now_seconds
    return now - modified_time > max_age_seconds


def _dataset_path_for_id(dataset_id: str, *, storage_root: Path) -> Path:
    stored_path = (storage_root / f"{dataset_id}.csv").resolve()
    if not stored_path.is_relative_to(storage_root):
        raise ValueError("Dataset path escaped controlled storage root.")
    return stored_path


def _ensure_storage_root(storage_root: Path) -> Path:
    root = _resolved_storage_root(storage_root)
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise DatasetStorageError(
            f"Failed to initialize dataset storage root '{root}'.",
        ) from error
    return root


def _resolved_storage_root(storage_root: Path) -> Path:
    return storage_root.resolve()


def _remove_temporary_file(temp_path: Path) -> None:
    try:
        temp_path.unlink(missing_ok=True)
    except OSError:
        pass
