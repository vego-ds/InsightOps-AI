from fastapi.testclient import TestClient
import json


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
    assert '"sequence":8' in content
    assert '"type":"run.final"' in content


def test_analysis_run_events_contains_artifact_events(client: TestClient) -> None:
    create_response = client.post("/api/analysis/runs", json=_valid_payload())
    run_id = create_response.json()["runId"]

    response = client.get(f"/api/analysis/runs/{run_id}/events")

    assert "event: run.artifact" in response.text


def test_analysis_run_artifact_payloads_are_safe_shapes(client: TestClient) -> None:
    create_response = client.post("/api/analysis/runs", json=_valid_payload())
    run_id = create_response.json()["runId"]

    response = client.get(f"/api/analysis/runs/{run_id}/events")
    artifacts = [
        _event_payload(line)
        for line in response.text.splitlines()
        if line.startswith("data: ") and '"type":"artifact"' in line
    ]

    assert len(artifacts) == 3
    assert all(artifact["version"] == "insightops.run-event.v1" for artifact in artifacts)

    table = next(item["artifact"] for item in artifacts if item["artifact"]["kind"] == "table")
    chart = next(item["artifact"] for item in artifacts if item["artifact"]["kind"] == "chart")
    markdown = next(
        item["artifact"] for item in artifacts if item["artifact"]["kind"] == "markdown"
    )

    assert table["columns"]
    assert table["rows"]
    assert chart["chartType"] in {"bar", "line"}
    assert isinstance(chart["xKey"], str)
    assert isinstance(chart["yKey"], str)
    assert chart["data"]
    assert isinstance(markdown["text"], str)
    assert "<" not in markdown["text"]


def _event_payload(data_line: str) -> dict:
    return json.loads(data_line.removeprefix("data: "))
