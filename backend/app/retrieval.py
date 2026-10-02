import uuid

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.embeddings import embed_texts
from app.models import Document, DocumentChunk, DocumentStatus


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    limit: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    page_number: int | None
    content: str
    distance: float


def search_chunks(session: Session, query: str, limit: int = 5) -> list[SearchResult]:
    query_embedding = embed_texts([query])[0]
    distance = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
    statement = (
        select(DocumentChunk, Document.filename, distance)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(Document.status == DocumentStatus.indexed, DocumentChunk.embedding.is_not(None))
        .order_by(distance)
        .limit(limit)
    )
    return [
        SearchResult(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            filename=filename,
            page_number=chunk.page_number,
            content=chunk.content,
            distance=float(chunk_distance),
        )
        for chunk, filename, chunk_distance in session.execute(statement)
    ]
