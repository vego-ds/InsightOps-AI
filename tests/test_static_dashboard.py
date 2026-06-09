from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_root_returns_html() -> None:
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    # Verify index.html contains workspace-oriented sections
    html_content = response.text
    assert "InsightOps-AI" in html_content
    assert 'href="/"' in html_content
    assert 'aria-label="Go to InsightOps-AI home"' in html_content
    assert "Data" in html_content
    assert "Ask" in html_content
    assert "Executive Summary" in html_content
    assert "Quality Gate" in html_content
    assert "Trends and Forecasts" in html_content
    assert "Visual Analytics" in html_content
    assert "Recommendations" in html_content
    assert "Reports" in html_content
    assert "Technical Evidence" in html_content

    # Sprint 30A new HTML components
    assert "Ask Guided Analytics" in html_content
    assert "Technical Evidence Drawer" in html_content
    assert "Composition Views" in html_content


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

    # Verify app.js contains functions or labels
    js_content = script_response.text
    assert "parseAskIntent" in js_content
    assert "executeAskIntent" in js_content
    assert "analysisHistory" in js_content
    assert "handleReportDownload" in js_content
    assert (
        "populateAnalysisResults" in js_content
    )  # quality gate / forecast / recs rendering
    assert "renderVisualAnalyticsCharts" in js_content  # visual analytics rendering

    # Sprint 30A/B new JS functions
    assert "validateAnalysisShape" in js_content
    assert "safeRenderSection" in js_content
    assert "renderPiePreview" in js_content
    assert "renderLinePreview" in js_content
    assert "renderHorizontalBarPreview" in js_content
    assert "renderCommandHelp" in js_content

    # Verify styles.css contains layout classes
    css_content = style_response.text
    assert "app-layout" in css_content  # workspace layout
    assert "sidebar" in css_content
    assert "command-panel" in css_content
    assert "result-card" in css_content
    assert "status-card" in css_content  # pytest compatibility
    assert "action-center" in css_content
    assert "tech-drawer" in css_content

    # Sprint 30A new CSS classes
    assert "visuals-gallery-controls" in css_content
    assert "pie-preview-wrapper" in css_content
    assert "svg-line-container" in css_content
    assert "suggestion-chip" in css_content
    assert "highlighted-section" in css_content
    assert "render-error-block" in css_content
    assert "empty-preview-msg" in css_content


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


def test_sample_report_export_works() -> None:
    client = TestClient(app)

    # Test PDF download
    pdf_res = client.post("/analysis/sample/report?format=pdf")
    assert pdf_res.status_code == 200

    # Test Markdown download
    md_res = client.post("/analysis/sample/report?format=markdown")
    assert md_res.status_code == 200


def test_dashboard_sprint_30c_ingestion_requirements() -> None:
    client = TestClient(app)

    # 1. HTML contains sample analysis and CSV upload controls
    html_res = client.get("/")
    assert html_res.status_code == 200
    html_content = html_res.text
    assert "run-sample-btn" in html_content
    assert "empty-state-sample-btn" in html_content
    assert "csv-file-input" in html_content

    # 2. app.js contains required keywords
    js_res = client.get("/static/app.js")
    assert js_res.status_code == 200
    js_content = js_res.text
    assert "runSampleAnalysis" in js_content
    assert "uploadSalesCSV" in js_content
    assert "FormData" in js_content
    assert '.append("file"' in js_content or ".append('file'" in js_content
    assert "/analysis/sample" in js_content
    assert "/analysis/upload" in js_content
    assert "currentAnalysis" in js_content
    assert "currentDataMode" in js_content
    assert "currentFile" in js_content

    # 3. GET /analysis/sample returns 200
    sample_res = client.get("/analysis/sample")
    assert sample_res.status_code == 200

    # 4. POST /analysis/upload returns 200 for valid file
    sample_csv = Path("data/sample/sales_sample.csv")
    with sample_csv.open("rb") as csv_file:
        upload_res = client.post(
            "/analysis/upload",
            files={"file": ("sales_sample.csv", csv_file, "text/csv")},
        )
    assert upload_res.status_code == 200

    # 5. POST /analysis/upload rejects non-CSV
    non_csv_res = client.post(
        "/analysis/upload",
        files={"file": ("sales.txt", b"hello", "text/plain")},
    )
    assert non_csv_res.status_code == 400

    # 6. POST /analysis/upload rejects empty upload
    empty_res = client.post(
        "/analysis/upload",
        files={"file": ("empty.csv", b"", "text/csv")},
    )
    assert empty_res.status_code == 400

    # 7. Report export endpoints still work
    pdf_res = client.post("/analysis/sample/report?format=pdf")
    assert pdf_res.status_code == 200


def test_dashboard_sprint_31_requirements() -> None:
    client = TestClient(app)

    # 1. HTML contains view mode controls
    html_res = client.get("/")
    assert html_res.status_code == 200
    html_content = html_res.text
    assert "view-mode-selector-bar" in html_content
    assert "Executive View" in html_content
    assert "Analyst View" in html_content
    assert "Audit View" in html_content

    # 2. app.js contains view mode functions
    js_res = client.get("/static/app.js")
    assert js_res.status_code == 200
    js_content = js_res.text
    assert "initializeViewModes" in js_content
    assert "setDashboardViewMode" in js_content
    assert "getCurrentViewMode" in js_content
    assert "getChartDisplayTier" in js_content
    assert "shouldShowTechnicalIdentifiers" in js_content

    # 3. PDF report starts with %PDF and includes expected sections
    pdf_report_res = client.post("/analysis/sample/report?format=pdf")
    assert pdf_report_res.status_code == 200
    pdf_bytes = pdf_report_res.content
    assert pdf_bytes.startswith(b"%PDF")

    # 4. Markdown report includes technical appendix and narrative
    md_report_res = client.post("/analysis/sample/report?format=markdown")
    assert md_report_res.status_code == 200
    md_text = md_report_res.text
    assert "# Executive Sales Report" in md_text
    assert "## Executive Summary" in md_text
    assert "## Decision Readiness" in md_text
    assert "## KPI Snapshot" in md_text
    assert "## Top Findings" in md_text
    assert "## Top Business Actions" in md_text
    assert "## Technical Appendix" in md_text
    assert "## Audit Events" in md_text
    assert "contains $446,250.00 in valid revenue" in md_text
