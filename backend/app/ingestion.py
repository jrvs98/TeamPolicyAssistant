from pathlib import Path

import fitz
import pytesseract
from PIL import Image

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150
OCR_DPI = 300


def _ocr_page(page: fitz.Page) -> str:
    matrix = fitz.Matrix(OCR_DPI / 72, OCR_DPI / 72)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
    return pytesseract.image_to_string(image).strip()


def extract_text(path: Path, content_type: str) -> list[tuple[int | None, str]]:
    if content_type == "application/pdf" or path.suffix.lower() == ".pdf":
        with fitz.open(path) as pdf:
            pages = []
            for page in pdf:
                text = page.get_text("text").strip()
                pages.append((page.number + 1, text or _ocr_page(page)))
            return pages

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
