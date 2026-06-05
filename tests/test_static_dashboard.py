from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_root_returns_html() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "InsightOps-AI" in response.text


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
