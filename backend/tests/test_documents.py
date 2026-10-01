from fastapi.testclient import TestClient

from app.events import DocumentUploadedEvent
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


def test_document_uploaded_event_has_versioned_contract() -> None:
    event = DocumentUploadedEvent.create(
        document_id="11111111-1111-1111-1111-111111111111",
        storage_key="document.pdf",
        filename="policy.pdf",
        content_type="application/pdf",
    )

    assert event.event_type == "document.uploaded.v1"
    assert event.model_dump()["filename"] == "policy.pdf"
