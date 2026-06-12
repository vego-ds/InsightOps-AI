from pathlib import Path
import shutil


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
