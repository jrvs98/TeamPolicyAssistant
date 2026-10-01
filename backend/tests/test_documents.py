from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_document_upload_requires_admin_authentication() -> None:
    response = client.post(
        "/api/v1/documents",
        files={"file": ("policy.md", b"# Policy", "text/markdown")},
    )

    assert response.status_code == 401


def test_document_listing_requires_admin_authentication() -> None:
    response = client.get("/api/v1/documents")

    assert response.status_code == 401
