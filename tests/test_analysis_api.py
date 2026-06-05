from fastapi.testclient import TestClient

from app.main import app


def test_analysis_sample_returns_validation_and_kpis() -> None:
    client = TestClient(app)

    response = client.get("/analysis/sample")

    assert response.status_code == 200

    payload = response.json()
    assert "validation" in payload
    assert "kpis" in payload
    assert "security" in payload
    assert "anomalies" in payload
    assert "audit_events" in payload

    validation = payload["validation"]
    assert validation["total_rows"] == 5
    assert validation["valid_rows"] == 3
    assert validation["invalid_rows"] == 2

    kpis = payload["kpis"]
    assert kpis["total_orders"] == 3
    assert kpis["total_revenue"] > 0

    security = payload["security"]
    assert security["prompt_injection_detected"] is False

    anomalies = payload["anomalies"]
    assert "total_anomalies" in anomalies
    assert "anomalies" in anomalies
    assert isinstance(anomalies["anomalies"], list)

    assert len(payload["audit_events"]) >= 1
