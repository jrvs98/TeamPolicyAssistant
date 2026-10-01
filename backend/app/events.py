import uuid
from datetime import UTC, datetime

from pydantic import BaseModel


class DocumentUploadedEvent(BaseModel):
    event_type: str = "document.uploaded.v1"
    document_id: uuid.UUID
    storage_key: str
    filename: str
    content_type: str
    occurred_at: datetime

    @classmethod
    def create(cls, document_id: uuid.UUID, storage_key: str, filename: str, content_type: str):
        return cls(
            document_id=document_id,
            storage_key=storage_key,
            filename=filename,
            content_type=content_type,
            occurred_at=datetime.now(UTC),
        )
