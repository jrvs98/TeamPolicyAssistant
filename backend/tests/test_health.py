from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_frontend_origin() -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})

    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_readiness(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "check_database", lambda: True)
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readiness_reports_database_failure(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "check_database", lambda: False)
    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "Database is unavailable"


def test_protected_endpoint_requires_bearer_token() -> None:
    response = client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing access token"


def test_protected_endpoint_rejects_malformed_token() -> None:
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status_code == 401
