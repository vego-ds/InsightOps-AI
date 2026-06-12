from fastapi.testclient import TestClient


def _valid_payload() -> dict:
    return {
        "version": "insightops.analysis-run-create.v1",
        "datasetId": "dataset-123",
        "message": "Summarize revenue.",
        "schema": [
            {
                "key": "revenue",
                "label": "revenue",
                "dataType": "number",
                "nullable": False,
            }
        ],
        "previewRows": [{"revenue": 1200.0}],
    }


def test_analysis_run_creation_returns_created_response(client: TestClient) -> None:
    response = client.post("/api/analysis/runs", json=_valid_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "insightops.analysis-run-created.v1"
    assert payload["status"] == "created"
    assert payload["runId"]
    assert payload["streamUrl"] == f"/api/analysis/runs/{payload['runId']}/events"


def test_analysis_run_creation_rejects_invalid_version(client: TestClient) -> None:
    response = client.post(
        "/api/analysis/runs",
        json={**_valid_payload(), "version": "wrong"},
    )

    assert response.status_code == 400


def test_analysis_run_creation_rejects_missing_message(client: TestClient) -> None:
    response = client.post(
        "/api/analysis/runs",
        json={**_valid_payload(), "message": "   "},
    )

    assert response.status_code == 400


def test_analysis_run_events_returns_event_stream(client: TestClient) -> None:
    create_response = client.post("/api/analysis/runs", json=_valid_payload())
    run_id = create_response.json()["runId"]

    response = client.get(f"/api/analysis/runs/{run_id}/events")

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]


def test_analysis_run_events_contains_final_event(client: TestClient) -> None:
    create_response = client.post("/api/analysis/runs", json=_valid_payload())
    run_id = create_response.json()["runId"]

    response = client.get(f"/api/analysis/runs/{run_id}/events")
    content = response.text

    assert "event: run.final" in content
    assert '"version":"insightops.run-event.v1"' in content
    assert f'"runId":"{run_id}"' in content
    assert '"sequence":5' in content
    assert '"type":"run.final"' in content
