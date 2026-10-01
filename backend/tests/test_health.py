from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness() -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_protected_endpoint_requires_bearer_token() -> None:
    response = client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing access token"


def test_protected_endpoint_rejects_malformed_token() -> None:
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status_code == 401
