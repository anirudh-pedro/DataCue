import pytest
from fastapi.testclient import TestClient

from core import config as core_config
from main import app
from services.otp_service import get_otp_service, reset_otp_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def configure_console_transport(monkeypatch):
    monkeypatch.setenv("EMAIL_TRANSPORT", "console")
    core_config.get_settings.cache_clear()
    reset_otp_service()
    yield
    reset_otp_service()
    core_config.get_settings.cache_clear()


def test_send_and_verify_flow(monkeypatch):
    service = get_otp_service()
    monkeypatch.setattr(service._rng, "randrange", lambda start, stop: 123456)

    send_response = client.post("/otp/send", json={"email": "user@example.com"})
    assert send_response.status_code == 200

    verify_response = client.post(
        "/otp/verify",
        json={"email": "user@example.com", "otp": "123456"},
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["success"] is True

    reuse_response = client.post(
        "/otp/verify",
        json={"email": "user@example.com", "otp": "123456"},
    )
    assert reuse_response.status_code == 400


def test_send_without_credentials_returns_503(monkeypatch):
    monkeypatch.setenv("EMAIL_TRANSPORT", "smtp")
    monkeypatch.delenv("EMAIL_USER", raising=False)
    monkeypatch.delenv("EMAIL_APP_PASSWORD", raising=False)
    core_config.get_settings.cache_clear()
    reset_otp_service()

    response = client.post("/otp/send", json={"email": "user@example.com"})
    assert response.status_code == 503
    assert "configured" in response.json()["detail"].lower()
