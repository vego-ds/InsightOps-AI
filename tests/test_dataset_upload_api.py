import math
from pathlib import Path

from fastapi.testclient import TestClient

from app import main


def test_dataset_upload_csv_returns_frontend_preview_contract(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(main, "DATASET_STORAGE_DIR", tmp_path)
    csv_bytes = (
        "name,amount,count,active,order_date,updated_at,missing,ratio\n"
        "North,12.5,2,true,2026-01-01,2026-01-01 08:30:00,,inf\n"
        "South,,3,false,2026-01-02,2026-01-02 09:45:00,,4.5\n"
    ).encode()

    response = client.post(
        "/api/datasets/upload",
        files={"file": ("sales.csv", csv_bytes, "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "insightops.file-preview.v1"
    assert payload["status"] == "ok"
    assert payload["warnings"] == []

    dataset = payload["dataset"]
    assert dataset["id"]
    assert dataset["fileName"] == "sales.csv"
    assert dataset["mimeType"] == "text/csv"
    assert dataset["sizeBytes"] == len(csv_bytes)
    assert dataset["rowCount"] == 2
    assert dataset["previewRowCount"] == 2
    assert dataset["columnCount"] == 8
    assert (tmp_path / f"{dataset['id']}.csv").exists()

    data_types = {column["key"]: column["dataType"] for column in dataset["columns"]}
    assert data_types == {
        "name": "string",
        "amount": "number",
        "count": "integer",
        "active": "boolean",
        "order_date": "date",
        "updated_at": "datetime",
        "missing": "unknown",
        "ratio": "number",
    }
    assert all(
        set(column) == {"key", "label", "dataType", "nullable", "sampleValues"}
        for column in dataset["columns"]
    )

    first_row = dataset["previewRows"][0]
    second_row = dataset["previewRows"][1]
    assert first_row["missing"] is None
    assert second_row["amount"] is None
    assert first_row["ratio"] is None
    assert not _contains_invalid_json_number(dataset["previewRows"])


def test_dataset_upload_rejects_non_csv_with_strict_error(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("sales.txt", b"name\nNorth\n", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "version": "insightops.file-preview.v1",
        "status": "error",
        "error": {
            "code": "UNSUPPORTED_FILE_TYPE",
            "message": "Only CSV files are supported.",
            "recoverable": True,
        },
    }


def _contains_invalid_json_number(value: object) -> bool:
    if isinstance(value, float):
        return math.isnan(value) or math.isinf(value)
    if isinstance(value, list):
        return any(_contains_invalid_json_number(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_invalid_json_number(item) for item in value.values())
    return False
