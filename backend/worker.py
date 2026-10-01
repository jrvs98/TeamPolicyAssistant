import asyncio
import logging

import aio_pika

from app.config import get_settings
from app.messaging import declare_ingestion_queue, parse_document_uploaded

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_message(message: aio_pika.IncomingMessage) -> None:
    async with message.process():
        event = parse_document_uploaded(message.body)
        logger.info("Received %s for document %s", event.event_type, event.document_id)
        # Text extraction, OCR, chunking, and embeddings are the next worker slice.


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
