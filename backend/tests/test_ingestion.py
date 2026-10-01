from pathlib import Path

import fitz

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