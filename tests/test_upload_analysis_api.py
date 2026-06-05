from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


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
    assert "validation" in payload
    assert "kpis" in payload
    assert "security" in payload
    assert "anomalies" in payload
    assert "charts" in payload
    assert "insights" in payload
    assert "audit_events" in payload


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
