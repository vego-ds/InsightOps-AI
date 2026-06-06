from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

EXPECTED_ANALYSIS_SECTIONS = {
    "source_metadata",
    "validation",
    "data_profile",
    "quality_score",
    "quality_gate",
    "preparation",
    "transformation_log",
    "manipulation_summary",
    "trend_analysis",
    "forecast_analysis",
    "kpis",
    "security",
    "anomalies",
    "charts",
    "insights",
    "recommendation_plan",
    "workflow_improvement_plan",
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
    assert payload["source_metadata"]["source_type"] == "uploaded_csv"
    assert payload["source_metadata"]["file_name"] == "sales_sample.csv"
    assert payload["data_profile"]["total_rows"] == 5
    assert payload["quality_score"]["grade"] == "fair"
    assert payload["quality_gate"]["status"] == "warning"
    assert payload["quality_gate"]["confidence_level"] == "medium"
    assert payload["preparation"]["total_records"] == 3
    assert payload["transformation_log"]["entries"]
    assert payload["manipulation_summary"]["ranked_products"]
    assert payload["trend_analysis"]["period_grain"] == "month"
    assert payload["trend_analysis"]["total_periods"] >= 1
    assert "readiness_status" in payload["forecast_analysis"]
    assert "confidence_level" in payload["forecast_analysis"]
    assert "next_period" in payload["forecast_analysis"]
    assert isinstance(payload["forecast_analysis"]["warnings"], list)
    assert isinstance(payload["forecast_analysis"]["recommended_actions"], list)
    first_chart = payload["charts"]["charts"][0]
    assert first_chart["business_question"]
    assert first_chart["interpretation"]
    assert isinstance(first_chart["related_insight_ids"], list)
    assert isinstance(first_chart["recommended_actions"], list)
    assert payload["recommendation_plan"]["total_recommendations"] >= 1
    assert payload["workflow_improvement_plan"]["total_workflows"] >= 1


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
