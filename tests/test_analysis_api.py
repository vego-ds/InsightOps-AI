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


def test_analysis_sample_returns_validation_and_kpis() -> None:
    client = TestClient(app)

    response = client.get("/analysis/sample")

    assert response.status_code == 200

    payload = response.json()
    assert set(payload) == EXPECTED_ANALYSIS_SECTIONS

    source_metadata = payload["source_metadata"]
    assert source_metadata["source_type"] == "sample_csv"
    assert source_metadata["record_count"] == 200

    validation = payload["validation"]
    assert validation["total_rows"] == 200
    assert validation["valid_rows"] == 198
    assert validation["invalid_rows"] == 2

    data_profile = payload["data_profile"]
    assert data_profile["total_rows"] == 200
    assert data_profile["unique_customers"] == 85
    assert "revenue_summary" in data_profile

    quality_score = payload["quality_score"]
    assert quality_score["score"] == 60
    assert quality_score["grade"] == "fair"

    quality_gate = payload["quality_gate"]
    assert quality_gate["status"] == "warning"
    assert quality_gate["confidence_level"] == "medium"
    assert "can_generate_kpis" in quality_gate
    assert "can_generate_charts" in quality_gate
    assert "can_generate_reports" in quality_gate
    assert "can_generate_llm_narrative" in quality_gate

    assert payload["preparation"]["total_records"] == 198
    assert len(payload["transformation_log"]["entries"]) >= 2
    assert "monthly_revenue" in payload["manipulation_summary"]

    trends = payload["trend_analysis"]
    assert trends["period_grain"] == "month"
    assert trends["total_periods"] >= 1
    assert "revenue_trend" in trends
    assert "average_discount_trend" in trends

    forecast = payload["forecast_analysis"]
    assert "readiness_status" in forecast
    assert "confidence_level" in forecast
    assert "next_period" in forecast
    assert isinstance(forecast["warnings"], list)
    assert isinstance(forecast["recommended_actions"], list)

    kpis = payload["kpis"]
    assert kpis["total_orders"] == 198
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
        assert "business_question" in chart
        assert "interpretation" in chart
        assert "related_insight_ids" in chart
        assert "recommended_actions" in chart
        assert "data" in chart

    insights = payload["insights"]
    assert "summary" in insights
    assert isinstance(insights["insights"], list)
    assert isinstance(insights["recommended_actions"], list)

    recommendation_plan = payload["recommendation_plan"]
    assert recommendation_plan["total_recommendations"] >= 1
    assert isinstance(recommendation_plan["recommendations"], list)

    workflow_improvement_plan = payload["workflow_improvement_plan"]
    assert workflow_improvement_plan["total_workflows"] >= 1
    assert isinstance(workflow_improvement_plan["workflows"], list)

    audit_events = payload["audit_events"]
    assert len(audit_events) >= 1
    assert any(event["event_type"] == "insights_generated" for event in audit_events)
