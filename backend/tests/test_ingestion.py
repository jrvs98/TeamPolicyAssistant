from pathlib import Path

import fitz
from PIL import Image, ImageDraw

from app.ingestion import chunk_text, extract_text


def test_markdown_text_is_chunked() -> None:
    chunks = chunk_text("  Policy   allows remote work. ")

    assert chunks == ["Policy allows remote work."]


def test_markdown_extraction(tmp_path: Path) -> None:
    path = tmp_path / "policy.md"
    path.write_text("# Remote work\nTwo days per week.", encoding="utf-8")

    assert extract_text(path, "text/markdown") == [(None, "# Remote work\nTwo days per week.")]


def test_pdf_extraction_includes_page_number(tmp_path: Path) -> None:
    path = tmp_path / "policy.pdf"
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), "Remote work is allowed.")
        pdf.save(path)

    pages = extract_text(path, "application/pdf")

    assert pages[0][0] == 1
    assert "Remote work is allowed." in pages[0][1]


def test_scanned_pdf_uses_ocr(tmp_path: Path) -> None:
    image_path = tmp_path / "page.png"
    image = Image.new("RGB", (1200, 300), "white")
    ImageDraw.Draw(image).text((60, 100), "Remote work policy", fill="black")
    image.save(image_path)
    pdf_path = tmp_path / "scanned.pdf"
    with fitz.open() as pdf:
        page = pdf.new_page(width=1200, height=300)
        page.insert_image(page.rect, filename=str(image_path))
        pdf.save(pdf_path)

    pages = extract_text(pdf_path, "application/pdf")

    assert pages[0][0] == 1
    assert "Remote work" in pages[0][1]