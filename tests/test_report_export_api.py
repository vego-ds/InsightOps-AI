from pathlib import Path

from fastapi.testclient import TestClient

import app.main as app_main
from app.main import app
from insightops.pipeline.sample_analysis import analyze_sample_sales_data


def test_sample_report_returns_pdf() -> None:
    client = TestClient(app)

    response = client.post("/analysis/sample/report")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert_report_headers(response, "pdf", "executive_sales_report.pdf")


def test_sample_report_returns_markdown() -> None:
    client = TestClient(app)

    response = client.post("/analysis/sample/report?format=markdown")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "Executive Sales Report" in response.text
    assert_report_headers(response, "markdown", "executive_sales_report.md")


def test_sample_report_accepts_markdown_alias() -> None:
    client = TestClient(app)

    response = client.post("/analysis/sample/report?format=md")

    assert response.status_code == 200
    assert response.headers["x-report-format"] == "markdown"


def test_sample_report_rejects_invalid_format() -> None:
    client = TestClient(app)

    response = client.post("/analysis/sample/report?format=xlsx")

    assert response.status_code == 400
    assert "Unsupported report format" in response.json()["detail"]


def test_upload_report_returns_pdf_for_valid_csv() -> None:
    client = TestClient(app)
    sample_csv = Path("data/sample/sales_sample.csv")

    with sample_csv.open("rb") as csv_file:
        response = client.post(
            "/analysis/upload/report?format=pdf",
            files={"file": ("sales_sample.csv", csv_file, "text/csv")},
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert_report_headers(response, "pdf", "executive_sales_report.pdf")


def test_upload_report_returns_markdown_for_valid_csv() -> None:
    client = TestClient(app)
    sample_csv = Path("data/sample/sales_sample.csv")

    with sample_csv.open("rb") as csv_file:
        response = client.post(
            "/analysis/upload/report?format=markdown",
            files={"file": ("sales_sample.csv", csv_file, "text/csv")},
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "Executive Sales Report" in response.text
    assert_report_headers(response, "markdown", "executive_sales_report.md")


def test_upload_report_rejects_non_csv_file() -> None:
    client = TestClient(app)

    response = client.post(
        "/analysis/upload/report",
        files={"file": ("sales.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400


def test_upload_report_rejects_empty_csv_file() -> None:
    client = TestClient(app)

    response = client.post(
        "/analysis/upload/report",
        files={"file": ("empty.csv", b"", "text/csv")},
    )

    assert response.status_code == 400


def test_upload_report_rejects_oversized_csv_file(monkeypatch) -> None:
    from app.main import settings

    monkeypatch.setattr(settings, "max_upload_bytes", 1_000_000)

    client = TestClient(app)
    oversized_content = b"a" * 1_000_001

    response = client.post(
        "/analysis/upload/report",
        files={"file": ("oversized.csv", oversized_content, "text/csv")},
    )

    assert response.status_code == 413


def test_upload_report_rejects_invalid_format_before_generation() -> None:
    client = TestClient(app)
    sample_csv = Path("data/sample/sales_sample.csv")

    with sample_csv.open("rb") as csv_file:
        response = client.post(
            "/analysis/upload/report?format=docx",
            files={"file": ("sales_sample.csv", csv_file, "text/csv")},
        )

    assert response.status_code == 400


def test_sample_report_returns_422_when_quality_gate_blocks(monkeypatch) -> None:
    client = TestClient(app)
    analysis = analyze_sample_sales_data()
    analysis.quality_gate.can_generate_reports = False

    monkeypatch.setattr(app_main, "analyze_sample_sales_data", lambda: analysis)

    response = client.post("/analysis/sample/report")

    assert response.status_code == 422
    assert "quality gate" in response.json()["detail"]


def assert_report_headers(response, report_format: str, file_name: str) -> None:
    assert "attachment" in response.headers["content-disposition"]
    assert file_name in response.headers["content-disposition"]
    assert response.headers["x-report-id"] == "executive_sales_report"
    assert response.headers["x-report-format"] == report_format
    assert int(response.headers["x-report-size-bytes"]) == len(response.content)
