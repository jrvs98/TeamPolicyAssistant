import hashlib
import math
import re
from collections.abc import Iterable

from app.config import get_settings


def _local_embedding(text: str, dimensions: int) -> list[float]:
    values = [0.0] * dimensions
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] & 1 else -1.0
        values[index] += sign
    magnitude = math.sqrt(sum(value * value for value in values))
    return [value / magnitude for value in values] if magnitude else values


def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    settings = get_settings()
    if settings.embedding_provider != "local":
        raise RuntimeError(f"Unsupported embedding provider: {settings.embedding_provider}")
    return [_local_embedding(text, settings.embedding_dimensions) for text in texts]
