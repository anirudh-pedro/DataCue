"""Integration smoke tests for orchestrator FastAPI app."""

import os
from io import BytesIO

from fastapi.testclient import TestClient

os.environ.setdefault("DISABLE_FIREBASE_AUTH", "true")

from main import app  # noqa: E402  (import after env configuration)

client = TestClient(app)
client.headers.update({"X-Debug-User": "test-user"})


def _upload_sample_dataset(path: str = "/ingestion/upload"):
    csv_content = b"category,value\nA,1\nB,2\n"
    files = {"file": ("sample.csv", BytesIO(csv_content), "text/csv")}
    response = client.post(path, files=files)
    assert response.status_code == 200
    return response.json()


def _create_chat_session() -> str:
    payload = {"email": "test@example.com", "display_name": "Test User"}
    response = client.post("/chat/sessions", json=payload)
    assert response.status_code == 200
    return response.json()["session_id"]


def test_root_health():
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "ingestion" in payload["agents"]


def test_ingestion_and_dashboard_flow():
    ingestion_result = _upload_sample_dataset()
    dataset_name = ingestion_result["dataset_name"]

    datasets_response = client.get("/ingestion/datasets")
    assert datasets_response.status_code == 200
    datasets = datasets_response.json()["datasets"]
    assert dataset_name in datasets

    dashboard_payload = {
        "data": ingestion_result["data"],
        "metadata": ingestion_result["metadata"],
        "options": {"dashboard_type": "overview", "generate_insights": False},
    }
    dashboard_response = client.post("/dashboard/generate", json=dashboard_payload)
    assert dashboard_response.status_code == 200
    dashboard_json = dashboard_response.json()
    assert dashboard_json["status"] == "success"


def test_knowledge_analyze_summary():
    session_id = _create_chat_session()
    ingestion_result = _upload_sample_dataset()
    payload = {
        "data": ingestion_result["data"],
        "generate_insights": False,
        "generate_recommendations": False,
        "session_id": session_id,
    }
    analyze_response = client.post("/knowledge/analyze", json=payload)
    assert analyze_response.status_code == 200
    summary_response = client.get(f"/knowledge/summary?session_id={session_id}")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert "dataset_size" in summary


def test_prediction_dataset_upload_and_list_models():
    upload_response = _upload_sample_dataset("/prediction/datasets/upload")
    assert "dataset_name" in upload_response
    models_response = client.get("/prediction/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert "models" in models_payload
