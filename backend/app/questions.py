from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import CurrentUser, require_authenticated
from app.database import get_db
from app.retrieval import SearchRequest, SearchResult, search_chunks

router = APIRouter(prefix="/api/v1/questions", tags=["questions"])


@router.post("/search", response_model=list[SearchResult])
def search_policy(
    request: SearchRequest,
    _: CurrentUser = Depends(require_authenticated),
    session: Session = Depends(get_db),
) -> list[SearchResult]:
    return search_chunks(session, request.query, request.limit)
