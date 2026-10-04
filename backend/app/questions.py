import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.answering import build_grounded_answer, run_answer_workflow
from app.auth import CurrentUser, require_admin, require_authenticated
from app.database import get_db
from app.models import Answer, Citation, EvaluationCase, EvaluationResult, Feedback, Question, User
from app.retrieval import SearchRequest, SearchResult, search_chunks

router = APIRouter(prefix="/api/v1/questions", tags=["questions"])
answers_router = APIRouter(prefix="/api/v1/answers", tags=["answers"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class AnswerResponse(BaseModel):
    question_id: str
    answer_id: str
    answer: str
    route: str
    citations: list[SearchResult]


class FeedbackRequest(BaseModel):
    value: str = Field(min_length=1, max_length=20)
    comment: str | None = Field(default=None, max_length=2000)


class EvaluationCaseResponse(BaseModel):
    id: str
    question: str
    expected_answer: str | None = None
    expected_document_ids: list[str] = []
    should_refuse: bool = False


_DEFAULT_EVALUATION_CASES = [
    {
        "question": "Can employees work remotely?",
        "expected_answer": "Remote work is allowed under the policy.",
        "expected_document_ids": [],
        "should_refuse": False,
    },
    {
        "question": "What is the expense reimbursement limit?",
        "expected_answer": "The policy defines the reimbursement cap.",
        "expected_document_ids": [],
        "should_refuse": False,
    },
    {
        "question": "What is the policy on alien life?",
        "expected_answer": None,
        "expected_document_ids": [],
        "should_refuse": True,
    },
]


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


@admin_router.get("/evaluations", response_model=list[EvaluationCaseResponse])
def list_evaluations(
    _: CurrentUser = Depends(require_admin),
    session: Session = Depends(get_db),
) -> list[EvaluationCaseResponse]:
    cases = session.scalars(select(EvaluationCase).order_by(EvaluationCase.question.asc())).all()
    if not cases:
        for payload in _DEFAULT_EVALUATION_CASES:
            session.add(EvaluationCase(**payload))
        session.commit()
        cases = session.scalars(select(EvaluationCase).order_by(EvaluationCase.question.asc())).all()
    return [
        EvaluationCaseResponse(
            id=str(case.id),
            question=case.question,
            expected_answer=case.expected_answer,
            expected_document_ids=[str(item) for item in case.expected_document_ids],
            should_refuse=case.should_refuse,
        )
        for case in cases
    ]


@admin_router.post("/evaluations/run")
def run_evaluations(
    _: CurrentUser = Depends(require_admin),
    session: Session = Depends(get_db),
) -> dict[str, object]:
    cases = session.scalars(select(EvaluationCase).order_by(EvaluationCase.question.asc())).all()
    if not cases:
        for payload in _DEFAULT_EVALUATION_CASES:
            session.add(EvaluationCase(**payload))
        session.commit()
        cases = session.scalars(select(EvaluationCase).order_by(EvaluationCase.question.asc())).all()

    results: list[dict[str, object]] = []
    passed_cases = 0
    for case in cases:
        hits = search_chunks(session, case.question, limit=5)
        retrieval_hit = bool(hits)
        refusal_ok = case.should_refuse == (not retrieval_hit or hits[0].distance > 0.95)
        score = 1.0 if refusal_ok and (case.should_refuse or retrieval_hit) else 0.5 if retrieval_hit else 0.0
        if score >= 0.5:
            passed_cases += 1
        result = EvaluationResult(
            case_id=case.id,
            metrics={
                "retrieval_hit": retrieval_hit,
                "refusal_ok": refusal_ok,
                "score": round(score, 2),
            },
        )
        session.add(result)
        results.append({"question": case.question, "score": round(score, 2), "passed": score >= 0.5})
    session.commit()
    average_score = round(sum(float(item["score"]) for item in results) / len(results), 2) if results else 0.0
    return {"cases_run": len(results), "passed_cases": passed_cases, "average_score": average_score, "results": results}


@router.post("/search", response_model=list[SearchResult])
def search_policy(
    request: SearchRequest,
    _: CurrentUser = Depends(require_authenticated),
    session: Session = Depends(get_db),
) -> list[SearchResult]:
    return search_chunks(session, request.query, request.limit)
