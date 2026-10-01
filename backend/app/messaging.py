import json

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message

from app.config import get_settings
from app.events import DocumentUploadedEvent

EXCHANGE_NAME = "policy.events"
QUEUE_NAME = "policy.document-ingestion"
ROUTING_KEY = "document.uploaded.v1"


async def publish_document_uploaded(event: DocumentUploadedEvent) -> None:
    settings = get_settings()
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    try:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(EXCHANGE_NAME, ExchangeType.TOPIC, durable=True)
        await exchange.publish(
            Message(
                body=event.model_dump_json().encode(),
                content_type="application/json",
                delivery_mode=DeliveryMode.PERSISTENT,
                message_id=str(event.document_id),
                type=event.event_type,
            ),
            routing_key=ROUTING_KEY,
        )
    finally:
        await connection.close()


async def declare_ingestion_queue(channel: aio_pika.abc.AbstractChannel) -> aio_pika.abc.AbstractQueue:
    exchange = await channel.declare_exchange(EXCHANGE_NAME, ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    await queue.bind(exchange, routing_key=ROUTING_KEY)
    return queue


def parse_document_uploaded(body: bytes) -> DocumentUploadedEvent:
    return DocumentUploadedEvent.model_validate(json.loads(body))
