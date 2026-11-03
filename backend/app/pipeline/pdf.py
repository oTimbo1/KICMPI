"""PDF → canonical Markdown (text-layer extraction, PyMuPDF).

Produces exactly the contract from TOOLING_SELECTION_AND_PIPELINE.md §3.4:
a ``# <title>`` header, a machine-parseable header block
(``source:`` / ``type:`` / ``pages:`` / ``language:``) and one
``## Page N`` section per text-bearing page.

The Markdown file is stored on the uploads volume for inspection/validation.
Downstream steps (chunking, embedding, storage, retrieval, summary) contain no
PDF knowledge — Markdown is the only format downstream (PLAN §4.1).
"""
from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF


class NoTextLayerError(Exception):
    """PDF has no extractable text (e.g. a scan) — v1 has no OCR path yet."""


def extract_markdown(pdf_path: Path, source_name: str, title: str) -> str:
    """Extract per-page text and assemble the canonical Markdown document.

    Raises NoTextLayerError when zero pages carry text.
    """
    doc = fitz.open(pdf_path)
    try:
        pages: list[tuple[int, str]] = []
        text_pages = 0
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if text:
                text_pages += 1
            pages.append((i, text))

        if text_pages == 0:
            raise NoTextLayerError(
                "Dit PDF heeft geen laaibare tekstlaag (scan?). "
                "Deze conceptversie ondersteunt nog geen OCR."
            )

        lines = [
            f"# {title}",
            "",
            f"source:   {source_name}",
            "type:     pdf",
            f"pages:    {len(pages)}",
            "language: nl",
            "",
        ]
        for i, text in pages:
            if not text:
                continue
            lines.append(f"## Page {i}")
            lines.append(text)
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"
    finally:
        doc.close()
