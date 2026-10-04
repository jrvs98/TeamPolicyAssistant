from fastapi.testclient import TestClient

from app.answering import build_grounded_answer, run_answer_workflow
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


def test_document_retry_requires_admin_authentication() -> None:
    response = client.post("/api/v1/documents/11111111-1111-1111-1111-111111111111/retry")

    assert response.status_code == 401


def test_policy_search_requires_authentication() -> None:
    response = client.post("/api/v1/questions/search", json={"query": "remote work"})

    assert response.status_code == 401


def test_answering_refuses_without_evidence() -> None:
    answer, route = build_grounded_answer("remote work", [])

    assert route == "fallback"
    assert "could not find enough evidence" in answer


def test_answer_feedback_requires_authentication() -> None:
    response = client.post(
        "/api/v1/answers/11111111-1111-1111-1111-111111111111/feedback",
        json={"value": "helpful"},
    )

    assert response.status_code == 401


def test_admin_evaluation_requires_admin_authentication() -> None:
    response = client.get("/api/v1/admin/evaluations")

    assert response.status_code == 401

    response = client.post("/api/v1/admin/evaluations/run")

    assert response.status_code == 401


def test_answer_workflow_tracks_bounded_steps() -> None:
    workflow = run_answer_workflow(
        "remote work",
        [
            type(
                "Result",
                (),
                {"content": "Remote work is allowed for eligible employees.", "distance": 0.42},
            )(),
            type(
                "Result",
                (),
                {"content": "Employees may work remotely two days per week.", "distance": 0.64},
            )(),
        ],
    )

    assert workflow["route"] == "extractive"
    assert workflow["steps"] == ["retrieve", "grade_context", "generate_answer", "verify_answer"]
    assert "Remote work" in workflow["answer"]
