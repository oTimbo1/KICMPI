"""Structure-aware chunking of canonical Markdown (PLAN §5.4 step 3).

Rules (deterministic, no source-format knowledge — Markdown in, chunks out):
  * natural boundaries: ``## Page N`` sections, then blank-line paragraphs;
  * target 256–512 tokens (token ≈ whitespace-split word);
  * ~15 % overlap: trailing sentences of a closed chunk are carried into the
    next chunk so no sentence is severed across a boundary;
  * a single paragraph longer than 512 words is hard-split on sentences.

Each chunk keeps its Markdown (including any ``## Page N`` headers it spans),
its first page number and a deterministic ``chunk_id = sha256(doc_id:chunk_index)``
(idempotent re-ingest → upsert overwrites the same points).
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

MIN_TOKENS = 200
MAX_TOKENS = 350
OVERLAP_FRACTION = 0.15
MIN_OVERLAP_WORDS = 20

# Note: "tokens" in the plan (256–512) are counted here as whitespace-split
# words (deterministic, per PLAN §5.4). Dutch text runs ≈1.3–1.4 BGE-M3
# tokens per word, so 200–350 words ≈ 280–480 real tokens — inside the
# 256–512-token band AND inside the llama.cpp physical-batch limit (512
# tokens) of the embedding server on the model system, so every chunk
# embeds in a single request (see embedding.py for the defensive fallback
# for any text that still exceeds it).

_PAGE_RE = re.compile(r"^## Page (\d+)\s*$", re.MULTILINE)
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    doc_id: str
    chunk_index: int
    page: int
    chunk_markdown: str

    @property
    def chunk_id(self) -> str:
        return hashlib.sha256(f"{self.doc_id}:{self.chunk_index}".encode("utf-8")).hexdigest()

    @property
    def words(self) -> int:
        return len(self.chunk_markdown.split())


def _parse_page_blocks(markdown: str) -> list[tuple[int, list[str]]]:
    """Split canonical Markdown into ``[(page, [block, ...]), ...]``.

    A block is a paragraph group (separated by blank lines) inside a page.
    The document header block (source:/type:/…) is not part of the chunks.
    """
    matches = list(_PAGE_RE.finditer(markdown))
    pages: list[tuple[int, list[str]]] = []
    for idx, m in enumerate(matches):
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown)
        body = markdown[start:end].strip()
        if not body:
            continue
        blocks = [b.strip() for b in re.split(r"\n\s*\n", body) if b.strip()]
        if blocks:
            pages.append((int(m.group(1)), blocks))
    return pages


def _units(markdown: str) -> list[tuple[int, str, bool]]:
    """Flat list of (page, block_text, is_first_block_of_page)."""
    units: list[tuple[int, str, bool]] = []
    for page, blocks in _parse_page_blocks(markdown):
        for j, block in enumerate(blocks):
            units.append((page, block, j == 0))
    return units


def _wc(parts: list[str]) -> int:
    return sum(len(p.split()) for p in parts)


def _sentences(text: str) -> list[str]:
    return [s for s in _SENT_SPLIT.split(text) if s.strip()]


def _last_paragraph(text: str) -> str:
    """Last blank-line block of a chunk, without a leading page header."""
    blocks = [b for b in text.rstrip().split("\n\n") if b.strip()]
    if not blocks:
        return ""
    lines = blocks[-1].splitlines()
    if lines and lines[0].startswith("## Page"):
        lines = lines[1:]
    return "\n".join(lines).strip()


def _carry_sentences(chunk_text: str) -> str:
    """~15 % trailing-sentence overlap for the next chunk."""
    budget = int(len(chunk_text.split()) * OVERLAP_FRACTION)
    if budget < MIN_OVERLAP_WORDS:
        return ""
    last = _last_paragraph(chunk_text)
    sentences = _sentences(last)
    carry: list[str] = []
    used = 0
    for s in reversed(sentences):
        w = len(s.split())
        if carry and used + w > budget:
            break
        carry.insert(0, s)
        used += w
        if used >= budget:
            break
    return " ".join(carry)


def _hard_split(text: str) -> list[str]:
    """Split an oversized block on sentence boundaries into ≤ MAX_TOKENS pieces."""
    if len(text.split()) <= MAX_TOKENS:
        return [text]
    pieces: list[str] = []
    cur: list[str] = []
    cur_words = 0
    for s in _sentences(text):
        w = len(s.split())
        if cur and cur_words + w > MAX_TOKENS:
            pieces.append(" ".join(cur))
            cur, cur_words = [], 0
        cur.append(s)
        cur_words += w
    if cur:
        pieces.append(" ".join(cur))
    return pieces or [text]


def chunk_markdown(markdown: str, doc_id: str) -> list[Chunk]:
    units = _units(markdown)
    if not units:
        return []

    raw: list[tuple[int, str]] = []  # (first_page, chunk_markdown)
    i, n = 0, len(units)
    carry = ""

    while i < n:
        parts: list[str] = []
        if carry:
            parts.append(carry)
            carry = ""
        first_page: int | None = None
        has_real = False

        while i < n:
            page, text, is_page_start = units[i]
            # Stop when adding this unit would exceed the max target —
            # unless the chunk has no real content yet (force it, then split).
            if has_real and _wc(parts) + len(text.split()) > MAX_TOKENS:
                break
            if first_page is None:
                first_page = page
            if is_page_start:
                parts.append(f"## Page {page}")
            parts.append(text)
            i += 1
            has_real = True
            if _wc(parts) >= MIN_TOKENS:
                break

        chunk_text = "\n\n".join(p for p in parts if p.strip()).strip()
        if not chunk_text or first_page is None:
            continue
        raw.append((first_page, chunk_text))
        carry = _carry_sentences(chunk_text)

    out: list[Chunk] = []
    for page, text in raw:
        for piece in _hard_split(text):
            out.append(
                Chunk(
                    doc_id=doc_id,
                    chunk_index=len(out),
                    page=page,
                    chunk_markdown=piece,
                )
            )
    return out
