from fastapi.testclient import TestClient

from app.main import app


def test_analysis_sample_returns_validation_and_kpis() -> None:
    client = TestClient(app)

    response = client.get("/analysis/sample")

    assert response.status_code == 200

    payload = response.json()
    assert "validation" in payload
    assert "kpis" in payload

    validation = payload["validation"]
    assert validation["total_rows"] == 5
    assert validation["valid_rows"] == 3
    assert validation["invalid_rows"] == 2

    kpis = payload["kpis"]
    assert kpis["total_orders"] == 3
    assert kpis["total_revenue"] > 0
