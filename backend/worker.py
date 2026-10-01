import asyncio
import logging

import aio_pika
from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.ingestion import chunk_text, extract_text
from app.messaging import declare_ingestion_queue, parse_document_uploaded
from app.models import Document, DocumentChunk, DocumentStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_message(message: aio_pika.IncomingMessage) -> None:
    async with message.process():
        event = parse_document_uploaded(message.body)
        logger.info("Received %s for document %s", event.event_type, event.document_id)
        settings = get_settings()
        path = settings.upload_path / event.storage_key
        with SessionLocal() as session:
            document = session.scalar(select(Document).where(Document.id == event.document_id))
            if document is None:
                logger.warning("Document %s no longer exists", event.document_id)
                return
            document.status = DocumentStatus.processing
            session.commit()
            try:
                pages = extract_text(path, event.content_type)
                chunks = [
                    DocumentChunk(document_id=document.id, chunk_index=index, content=chunk, page_number=page)
                    for page, text in pages
                    for index, chunk in enumerate(chunk_text(text))
                ]
                if not chunks:
                    raise ValueError("No text could be extracted from document")
                session.add_all(chunks)
                document.status = DocumentStatus.indexed
                document.failure_reason = None
                session.commit()
            except Exception as error:
                session.rollback()
                document.status = DocumentStatus.failed
                document.failure_reason = str(error)[:1000]
                session.commit()
                raise


async def run_worker() -> None:
    connection = await aio_pika.connect_robust(get_settings().rabbitmq_url)
    channel = await connection.channel()
    queue = await declare_ingestion_queue(channel)
    logger.info("Listening on %s", queue.name)
    await queue.consume(process_message)
    try:
        await asyncio.Future()
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(run_worker())
