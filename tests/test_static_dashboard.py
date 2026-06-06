from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_root_returns_html() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "InsightOps-AI" in response.text
    assert "Executive Summary" in response.text
    assert "Business Actions" in response.text
    assert "Forecast and Trend Snapshot" in response.text
    assert "Visual Analytics" in response.text
    assert "Technical Evidence" in response.text
    assert "report-format" in response.text
    assert "Download Sample Report" in response.text
    assert "Download Upload Report" in response.text


def test_dashboard_static_files_exist() -> None:
    static_dir = Path("app/static")

    assert (static_dir / "index.html").exists()
    assert (static_dir / "styles.css").exists()
    assert (static_dir / "app.js").exists()


def test_dashboard_static_assets_are_served() -> None:
    client = TestClient(app)

    script_response = client.get("/static/app.js")
    style_response = client.get("/static/styles.css")

    assert script_response.status_code == 200
    assert style_response.status_code == 200
    assert "renderExecutiveSummary" in script_response.text
    assert "renderStatusCards" in script_response.text
    assert "renderTopRecommendations" in script_response.text
    assert "renderForecastTrendSnapshot" in script_response.text
    assert "runReportDownload" in script_response.text
    assert "URL.createObjectURL" in script_response.text
    assert "/analysis/sample/report" in script_response.text
    assert "/analysis/upload/report" in script_response.text
    assert "Source Metadata" in script_response.text
    assert "Data Preparation" in script_response.text
    assert "Transformation Lineage" in script_response.text
    assert "Manipulation Summary" in script_response.text
    assert "Trend Analysis" in script_response.text
    assert "Forecast Analysis" in script_response.text
    assert "forecast_analysis" in script_response.text
    assert "Data Profile" in script_response.text
    assert "Quality Score" in script_response.text
    assert "Quality Gate" in script_response.text
    assert "Visual Analytics" in script_response.text
    assert "Business question" in script_response.text
    assert "Business Actions" in script_response.text
    assert "Workflow Improvements" in script_response.text
    assert "Visual Analytics" in script_response.text
    assert "workflow_improvement_plan" in script_response.text
    assert "recommendation_plan" in script_response.text
    assert "quality_gate" in script_response.text
    assert "status-card" in style_response.text
    assert "priority-badge" in style_response.text
    assert "technical-section" in style_response.text
    assert "report-actions" in style_response.text


def test_sample_analysis_still_works() -> None:
    client = TestClient(app)

    response = client.get("/analysis/sample")

    assert response.status_code == 200


def test_upload_analysis_still_works_for_valid_csv() -> None:
    client = TestClient(app)
    sample_csv = Path("data/sample/sales_sample.csv")

    with sample_csv.open("rb") as csv_file:
        response = client.post(
            "/analysis/upload",
            files={"file": ("sales_sample.csv", csv_file, "text/csv")},
        )

    assert response.status_code == 200
