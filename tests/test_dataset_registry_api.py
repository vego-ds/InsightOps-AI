from pathlib import Path

from fastapi.testclient import TestClient

from app import main
from insightops.datasets import clear_dataset_registry, get_dataset, get_dataset_path


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
