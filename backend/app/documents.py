import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import CurrentUser, require_admin
from app.config import get_settings
from app.database import get_db
from app.events import DocumentUploadedEvent
from app.messaging import publish_document_uploaded
from app.models import Document, DocumentStatus, User

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])
ALLOWED_TYPES = {"application/pdf", "text/markdown", "text/plain"}
ALLOWED_SUFFIXES = {".pdf", ".md", ".markdown"}


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str
    status: DocumentStatus


def _validate_upload(file: UploadFile) -> None:
    suffix = Path(file.filename or "").suffix.lower()
    if file.content_type not in ALLOWED_TYPES and suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Only PDF and Markdown files are supported")


def _get_or_create_user(session: Session, current_user: CurrentUser) -> User:
    user = session.scalar(select(User).where(User.subject == current_user.subject))
    if user is None:
        user = User(subject=current_user.subject, username=current_user.username)
        session.add(user)
        session.flush()
    return user


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_admin),
    session: Session = Depends(get_db),
) -> Document:
    _validate_upload(file)
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    document_id = uuid.uuid4()
    storage_key = f"{document_id}{Path(file.filename or '').suffix.lower()}"
    destination = upload_dir / storage_key
    total_bytes = 0

    try:
        with destination.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > settings.max_upload_bytes:
                    raise HTTPException(status_code=413, detail="File exceeds the upload size limit")
                output.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    user = _get_or_create_user(session, current_user)
    document = Document(
        id=document_id,
        filename=Path(file.filename or storage_key).name,
        content_type=file.content_type or "application/octet-stream",
        storage_key=storage_key,
        status=DocumentStatus.uploaded,
        uploaded_by=user.id,
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    await publish_document_uploaded(
        DocumentUploadedEvent.create(
            document_id=document.id,
            storage_key=document.storage_key,
            filename=document.filename,
            content_type=document.content_type,
        )
    )
    return document


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    _: CurrentUser = Depends(require_admin),
    session: Session = Depends(get_db),
) -> list[Document]:
    return list(session.scalars(select(Document).order_by(Document.created_at.desc())))
