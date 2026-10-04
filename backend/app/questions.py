import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.answering import build_grounded_answer, run_answer_workflow
from app.auth import CurrentUser, require_authenticated
from app.database import get_db
from app.models import Answer, Citation, Feedback, Question, User
from app.retrieval import SearchRequest, SearchResult, search_chunks

router = APIRouter(prefix="/api/v1/questions", tags=["questions"])
answers_router = APIRouter(prefix="/api/v1/answers", tags=["answers"])


class AnswerResponse(BaseModel):
    question_id: str
    answer_id: str
    answer: str
    route: str
    citations: list[SearchResult]


class FeedbackRequest(BaseModel):
    value: str = Field(min_length=1, max_length=20)
    comment: str | None = Field(default=None, max_length=2000)


def _get_or_create_user(session: Session, current_user: CurrentUser) -> User:
    user = session.scalar(select(User).where(User.subject == current_user.subject))
    if user is None:
        user = User(subject=current_user.subject, username=current_user.username)
        session.add(user)
        session.flush()
    return user


@router.post("", response_model=AnswerResponse)
def ask_policy(
    request: SearchRequest,
    current_user: CurrentUser = Depends(require_authenticated),
    session: Session = Depends(get_db),
) -> AnswerResponse:
    results = search_chunks(session, request.query, request.limit)
    workflow = run_answer_workflow(request.query, results)
    answer_text = str(workflow["answer"])
    route = str(workflow["route"])
    user = _get_or_create_user(session, current_user)
    question = Question(asked_by=user.id, text=request.query)
    session.add(question)
    session.flush()
    answer = Answer(question_id=question.id, text=answer_text, graph_route=route, model_name=None)
    session.add(answer)
    session.flush()
    for citation_order, result in enumerate(results[:3], start=1):
        session.add(Citation(answer_id=answer.id, chunk_id=result.chunk_id, citation_order=citation_order))
    session.commit()
    return AnswerResponse(
        question_id=str(question.id),
        answer_id=str(answer.id),
        answer=answer_text,
        route=route,
        citations=results[:3],
    )


@router.get("/{question_id}/events")
def question_events(question_id: str) -> StreamingResponse:
    def stream() -> object:
        for step in ["retrieve", "grade_context", "generate_answer", "verify_answer"]:
            yield f"event: step\ndata: {step}\n\n"
        yield "event: done\ndata: completed\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@answers_router.post("/{answer_id}/feedback")
def submit_answer_feedback(
    answer_id: str,
    request: FeedbackRequest,
    current_user: CurrentUser = Depends(require_authenticated),
    session: Session = Depends(get_db),
) -> dict[str, str]:
    try:
        parsed_answer_id = uuid.UUID(answer_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid answer id") from exc

    value = request.value.lower()
    if value not in {"helpful", "unhelpful", "up", "down", "positive", "negative"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Feedback value must be helpful or unhelpful")

    answer = session.get(Answer, parsed_answer_id)
    if answer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")

    user = _get_or_create_user(session, current_user)
    session.add(Feedback(answer_id=answer.id, user_id=user.id, value=value, comment=request.comment))
    session.commit()
    return {"status": "ok", "value": value}


@router.post("/search", response_model=list[SearchResult])
def search_policy(
    request: SearchRequest,
    _: CurrentUser = Depends(require_authenticated),
    session: Session = Depends(get_db),
) -> list[SearchResult]:
    return search_chunks(session, request.query, request.limit)
