from fastapi.testclient import TestClient

from app.main import app

EXPECTED_ANALYSIS_SECTIONS = {
    "source_metadata",
    "validation",
    "data_profile",
    "quality_score",
    "preparation",
    "transformation_log",
    "manipulation_summary",
    "kpis",
    "security",
    "anomalies",
    "charts",
    "insights",
    "audit_events",
}


def test_analysis_sample_returns_validation_and_kpis() -> None:
    client = TestClient(app)

    response = client.get("/analysis/sample")

    assert response.status_code == 200

    payload = response.json()
    assert set(payload) == EXPECTED_ANALYSIS_SECTIONS

    source_metadata = payload["source_metadata"]
    assert source_metadata["source_type"] == "sample_csv"
    assert source_metadata["record_count"] == 5

    validation = payload["validation"]
    assert validation["total_rows"] == 5
    assert validation["valid_rows"] == 3
    assert validation["invalid_rows"] == 2

    data_profile = payload["data_profile"]
    assert data_profile["total_rows"] == 5
    assert data_profile["unique_customers"] == 3
    assert "revenue_summary" in data_profile

    quality_score = payload["quality_score"]
    assert quality_score["score"] == 70
    assert quality_score["grade"] == "fair"

    assert payload["preparation"]["total_records"] == 3
    assert len(payload["transformation_log"]["entries"]) >= 2
    assert "monthly_revenue" in payload["manipulation_summary"]

    kpis = payload["kpis"]
    assert kpis["total_orders"] == 3
    assert kpis["total_revenue"] > 0

    security = payload["security"]
    assert security["prompt_injection_detected"] is False

    anomalies = payload["anomalies"]
    assert "total_anomalies" in anomalies
    assert "anomalies" in anomalies
    assert isinstance(anomalies["anomalies"], list)

    charts = payload["charts"]
    assert isinstance(charts["charts"], list)
    assert len(charts["charts"]) >= 4

    for chart in charts["charts"]:
        assert "chart_id" in chart
        assert "title" in chart
        assert "chart_type" in chart
        assert "metric" in chart
        assert "x_axis" in chart
        assert "y_axis" in chart
        assert "data" in chart

    insights = payload["insights"]
    assert "summary" in insights
    assert isinstance(insights["insights"], list)
    assert isinstance(insights["recommended_actions"], list)

    audit_events = payload["audit_events"]
    assert len(audit_events) >= 1
    assert any(
        event["event_type"] == "insights_generated"
        for event in audit_events
    )
