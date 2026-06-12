from fastapi.testclient import TestClient


def test_analysis_request_returns_placeholder_response(client: TestClient) -> None:
    response = client.post(
        "/api/analysis/request",
        json={
            "version": "insightops.analysis-request.v1",
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
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "insightops.analysis-response.v1"
    assert payload["status"] == "accepted"
    assert payload["runId"]
    assert "Backend analysis execution" in payload["assistantMessage"]


def test_analysis_request_rejects_wrong_version(client: TestClient) -> None:
    response = client.post(
        "/api/analysis/request",
        json={
            "version": "wrong",
            "datasetId": "dataset-123",
            "message": "Summarize revenue.",
            "schema": [],
            "previewRows": [],
        },
    )

    assert response.status_code == 400


def test_analysis_request_rejects_empty_dataset_id_or_message(
    client: TestClient,
) -> None:
    base_payload = {
        "version": "insightops.analysis-request.v1",
        "datasetId": "dataset-123",
        "message": "Summarize revenue.",
        "schema": [],
        "previewRows": [],
    }

    empty_dataset_response = client.post(
        "/api/analysis/request",
        json={**base_payload, "datasetId": "   "},
    )
    empty_message_response = client.post(
        "/api/analysis/request",
        json={**base_payload, "message": "   "},
    )

    assert empty_dataset_response.status_code == 400
    assert empty_message_response.status_code == 400
