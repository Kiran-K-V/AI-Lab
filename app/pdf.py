"""PDF helpers shared by both extractors."""

import io
from pathlib import Path

import pdfplumber
import pypdfium2


class ExtractionError(Exception):
    """Could not turn a document into a valid LabReport."""


def read_text(path: Path) -> str:
    """Text layer of every page, one line per visual row. Empty for scanned PDFs."""
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def render_pages(path: Path, scale: float = 2, max_pages: int = 5) -> list[bytes]:
    """Pages as grayscale JPEGs (small enough for an API request)."""
    pdf = pypdfium2.PdfDocument(path)
    pages = []
    for i in range(min(len(pdf), max_pages)):
        img = pdf[i].render(scale=scale).to_pil().convert("L")
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=80)
        pages.append(buf.getvalue())
    return pages
