from fastapi.testclient import TestClient

from app.main import app


def test_openapi_schema_documents_expected_api_contracts() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()
    assert schema["info"]["title"] == "InsightOps-AI"
    assert schema["info"]["version"] == "0.13.0"

    paths = schema["paths"]
    assert "/health" in paths
    assert "/analysis/sample" in paths
    assert "/analysis/upload" in paths
    assert "/analysis/sample/report" in paths
    assert "/analysis/upload/report" in paths

    assert "200" in paths["/analysis/sample"]["get"]["responses"]
    assert "400" in paths["/analysis/upload"]["post"]["responses"]
    assert "413" in paths["/analysis/upload"]["post"]["responses"]
    assert "200" in paths["/analysis/sample/report"]["post"]["responses"]
    assert "400" in paths["/analysis/sample/report"]["post"]["responses"]
    assert "422" in paths["/analysis/sample/report"]["post"]["responses"]
    assert "200" in paths["/analysis/upload/report"]["post"]["responses"]
    assert "400" in paths["/analysis/upload/report"]["post"]["responses"]
    assert "413" in paths["/analysis/upload/report"]["post"]["responses"]
    assert "422" in paths["/analysis/upload/report"]["post"]["responses"]

    components = schema["components"]["schemas"]
    assert "AnalysisResponse" in components
    assert "ErrorResponse" in components
    assert "HealthResponse" in components

    analysis_properties = components["AnalysisResponse"]["properties"]
    assert "source_metadata" in analysis_properties
    assert "data_profile" in analysis_properties
    assert "quality_score" in analysis_properties
    assert "quality_gate" in analysis_properties
    assert "preparation" in analysis_properties
    assert "transformation_log" in analysis_properties
    assert "manipulation_summary" in analysis_properties
    assert "trend_analysis" in analysis_properties
    assert "forecast_analysis" in analysis_properties
    assert "recommendation_plan" in analysis_properties
    assert "workflow_improvement_plan" in analysis_properties

    chart_properties = components["ChartSeries"]["properties"]
    assert "business_question" in chart_properties
    assert "interpretation" in chart_properties
    assert "related_insight_ids" in chart_properties
    assert "recommended_actions" in chart_properties
    assert "secondary_value" in components["ChartDataPoint"]["properties"]

    anomaly_properties = components["SalesAnomaly"]["properties"]
    assert "method" in anomaly_properties
    assert "threshold" in anomaly_properties
    assert "comparison" in anomaly_properties
