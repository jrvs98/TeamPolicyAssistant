from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.answering import build_grounded_answer, run_answer_workflow
from app.auth import CurrentUser, require_authenticated
from app.database import get_db
from app.models import Answer, Citation, Question, User
from app.retrieval import SearchRequest, SearchResult, search_chunks

router = APIRouter(prefix="/api/v1/questions", tags=["questions"])


class AnswerResponse(BaseModel):
    question_id: str
    answer_id: str
    answer: str
    route: str
    citations: list[SearchResult]


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


@router.post("/search", response_model=list[SearchResult])
def search_policy(
    request: SearchRequest,
    _: CurrentUser = Depends(require_authenticated),
    session: Session = Depends(get_db),
) -> list[SearchResult]:
    return search_chunks(session, request.query, request.limit)
