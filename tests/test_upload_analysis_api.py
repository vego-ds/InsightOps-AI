from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

EXPECTED_ANALYSIS_SECTIONS = {
    "validation",
    "kpis",
    "security",
    "anomalies",
    "charts",
    "insights",
    "audit_events",
}


def test_upload_analysis_accepts_valid_csv() -> None:
    client = TestClient(app)
    sample_csv = Path("data/sample/sales_sample.csv")

    with sample_csv.open("rb") as csv_file:
        response = client.post(
            "/analysis/upload",
            files={"file": ("sales_sample.csv", csv_file, "text/csv")},
        )

    assert response.status_code == 200

    payload = response.json()
    assert set(payload) == EXPECTED_ANALYSIS_SECTIONS


def test_upload_analysis_rejects_non_csv_file() -> None:
    client = TestClient(app)

    response = client.post(
        "/analysis/upload",
        files={"file": ("sales.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400


def test_upload_analysis_rejects_empty_csv_file() -> None:
    client = TestClient(app)

    response = client.post(
        "/analysis/upload",
        files={"file": ("empty.csv", b"", "text/csv")},
    )

    assert response.status_code == 400


def test_upload_analysis_rejects_oversized_csv_file() -> None:
    client = TestClient(app)
    oversized_content = b"a" * 1_000_001

    response = client.post(
        "/analysis/upload",
        files={"file": ("oversized.csv", oversized_content, "text/csv")},
    )

    assert response.status_code == 413
