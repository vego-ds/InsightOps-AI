from pathlib import Path
import shutil
import time


DATASET_STORAGE_ROOT = Path("scratch/datasets")


def save_dataset_file(
    source_path: Path,
    *,
    dataset_id: str,
    storage_root: Path = DATASET_STORAGE_ROOT,
) -> Path:
    root = storage_root.resolve()
    root.mkdir(parents=True, exist_ok=True)

    stored_path = (root / f"{dataset_id}.csv").resolve()
    if not stored_path.is_relative_to(root):
        raise ValueError("Dataset path escaped controlled storage root.")

    shutil.copyfile(source_path, stored_path)
    return stored_path


def validate_dataset_path_inside_root(
    dataset_path: Path,
    *,
    storage_root: Path = DATASET_STORAGE_ROOT,
) -> Path:
    root = storage_root.resolve()
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
    safe_path.unlink(missing_ok=True)


def dataset_file_is_expired(
    dataset_path: Path,
    *,
    max_age_seconds: int,
    now_seconds: float | None = None,
) -> bool:
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds must be non-negative.")

    if not dataset_path.exists():
        return True

    now = time.time() if now_seconds is None else now_seconds
    return now - dataset_path.stat().st_mtime > max_age_seconds
