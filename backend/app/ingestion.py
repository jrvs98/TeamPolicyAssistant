from pathlib import Path

import fitz

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150


def extract_text(path: Path, content_type: str) -> list[tuple[int | None, str]]:
    if content_type == "application/pdf" or path.suffix.lower() == ".pdf":
        with fitz.open(path) as pdf:
            return [(page.number + 1, page.get_text("text").strip()) for page in pdf]

    return [(None, path.read_text(encoding="utf-8"))]


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + size, len(normalized))
        chunks.append(normalized[start:end])
        if end == len(normalized):
            break
        start = end - overlap
    return chunks
