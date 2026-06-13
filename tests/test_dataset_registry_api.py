from pathlib import Path
import os
import time

from fastapi.testclient import TestClient

from app import main
from insightops.datasets import (
    DatasetMetadata,
    cleanup_datasets_older_than,
    clear_dataset_registry,
    get_dataset,
    get_dataset_path,
    register_dataset,
)


def test_dataset_upload_registers_dataset(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    clear_dataset_registry()
    monkeypatch.setattr(main, "DATASET_STORAGE_DIR", tmp_path)

    response = client.post(
        "/api/datasets/upload",
        files={"file": ("sales.csv", b"region,revenue\nNorth,1200\n", "text/csv")},
    )

    assert response.status_code == 200
    dataset = response.json()["dataset"]
    registered = get_dataset(dataset["id"])

    assert registered is not None
    assert registered.dataset_id == dataset["id"]
    assert registered.file_name == "sales.csv"
    assert registered.size_bytes == len(b"region,revenue\nNorth,1200\n")


def test_uploaded_dataset_can_be_resolved_by_dataset_id(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    clear_dataset_registry()
    monkeypatch.setattr(main, "DATASET_STORAGE_DIR", tmp_path)

    response = client.post(
        "/api/datasets/upload",
        files={"file": ("sales.csv", b"region,revenue\nNorth,1200\n", "text/csv")},
    )
    dataset_id = response.json()["dataset"]["id"]

    dataset_path = get_dataset_path(dataset_id)

    assert dataset_path is not None
    assert dataset_path.exists()
    assert dataset_path.read_text(encoding="utf-8") == "region,revenue\nNorth,1200\n"


def test_analysis_run_creation_rejects_unknown_dataset_id(client: TestClient) -> None:
    clear_dataset_registry()

    response = client.post(
        "/api/analysis/runs",
        json={
            "version": "insightops.analysis-run-create.v1",
            "datasetId": "missing-dataset",
            "message": "Summarize revenue.",
            "schema": [],
            "previewRows": [],
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Unknown datasetId.",
        "error_code": "UNKNOWN_DATASET",
    }


def test_dataset_path_remains_inside_controlled_storage_root(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    clear_dataset_registry()
    monkeypatch.setattr(main, "DATASET_STORAGE_DIR", tmp_path)

    response = client.post(
        "/api/datasets/upload",
        files={"file": ("sales.csv", b"region,revenue\nNorth,1200\n", "text/csv")},
    )
    dataset_id = response.json()["dataset"]["id"]

    dataset_path = get_dataset_path(dataset_id)

    assert dataset_path is not None
    assert dataset_path.is_relative_to(tmp_path.resolve())


def test_delete_registered_dataset_succeeds(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    clear_dataset_registry()
    monkeypatch.setattr(main, "DATASET_STORAGE_DIR", tmp_path)
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("sales.csv", b"region,revenue\nNorth,1200\n", "text/csv")},
    )
    dataset_id = response.json()["dataset"]["id"]

    delete_response = client.delete(f"/api/datasets/{dataset_id}")

    assert delete_response.status_code == 200
    assert delete_response.json() == {
        "version": "insightops.dataset-delete.v1",
        "status": "deleted",
        "datasetId": dataset_id,
    }


def test_delete_registered_dataset_removes_file_and_registry_entry(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    clear_dataset_registry()
    monkeypatch.setattr(main, "DATASET_STORAGE_DIR", tmp_path)
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("sales.csv", b"region,revenue\nNorth,1200\n", "text/csv")},
    )
    dataset_id = response.json()["dataset"]["id"]
    dataset_path = get_dataset_path(dataset_id)

    delete_response = client.delete(f"/api/datasets/{dataset_id}")

    assert delete_response.status_code == 200
    assert dataset_path is not None
    assert not dataset_path.exists()
    assert get_dataset(dataset_id) is None
    assert get_dataset_path(dataset_id) is None


def test_delete_unknown_dataset_id_is_rejected(client: TestClient) -> None:
    clear_dataset_registry()

    response = client.delete("/api/datasets/missing-dataset")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Unknown datasetId.",
        "error_code": "UNKNOWN_DATASET",
    }


def test_delete_rejects_unsafe_registered_path(
    client: TestClient,
    tmp_path: Path,
) -> None:
    clear_dataset_registry()
    unsafe_file = tmp_path.parent / "outside.csv"
    unsafe_file.write_text("region,revenue\nNorth,1200\n", encoding="utf-8")
    register_dataset(
        DatasetMetadata(
            dataset_id="unsafe-dataset",
            file_name="outside.csv",
            mime_type="text/csv",
            size_bytes=unsafe_file.stat().st_size,
            path=unsafe_file,
            storage_root=tmp_path,
        )
    )

    response = client.delete("/api/datasets/unsafe-dataset")

    assert response.status_code == 400
    assert response.json()["error_code"] == "UNSAFE_DATASET_PATH"
    assert unsafe_file.exists()
    assert get_dataset("unsafe-dataset") is not None


def test_cleanup_removes_expired_datasets(tmp_path: Path) -> None:
    clear_dataset_registry()
    old_file = tmp_path / "old.csv"
    old_file.write_text("region,revenue\nNorth,1200\n", encoding="utf-8")
    old_timestamp = time.time() - 3_600
    os.utime(old_file, (old_timestamp, old_timestamp))
    register_dataset(
        DatasetMetadata(
            dataset_id="old-dataset",
            file_name="old.csv",
            mime_type="text/csv",
            size_bytes=old_file.stat().st_size,
            path=old_file,
            storage_root=tmp_path,
        )
    )

    removed = cleanup_datasets_older_than(60)

    assert [dataset.dataset_id for dataset in removed] == ["old-dataset"]
    assert not old_file.exists()
    assert get_dataset("old-dataset") is None


def test_cleanup_preserves_fresh_datasets(tmp_path: Path) -> None:
    clear_dataset_registry()
    fresh_file = tmp_path / "fresh.csv"
    fresh_file.write_text("region,revenue\nNorth,1200\n", encoding="utf-8")
    register_dataset(
        DatasetMetadata(
            dataset_id="fresh-dataset",
            file_name="fresh.csv",
            mime_type="text/csv",
            size_bytes=fresh_file.stat().st_size,
            path=fresh_file,
            storage_root=tmp_path,
        )
    )

    removed = cleanup_datasets_older_than(60)

    assert removed == []
    assert fresh_file.exists()
    assert get_dataset("fresh-dataset") is not None
