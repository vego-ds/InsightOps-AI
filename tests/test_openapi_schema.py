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

    assert "200" in paths["/analysis/sample"]["get"]["responses"]
    assert "400" in paths["/analysis/upload"]["post"]["responses"]
    assert "413" in paths["/analysis/upload"]["post"]["responses"]

    components = schema["components"]["schemas"]
    assert "AnalysisResponse" in components
    assert "ErrorResponse" in components
    assert "HealthResponse" in components

    analysis_properties = components["AnalysisResponse"]["properties"]
    assert "source_metadata" in analysis_properties
    assert "data_profile" in analysis_properties
    assert "quality_score" in analysis_properties
    assert "preparation" in analysis_properties
    assert "transformation_log" in analysis_properties
    assert "manipulation_summary" in analysis_properties
