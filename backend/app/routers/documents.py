"""Documents: upload, list, get, delete, original-file download + background
ingestion (PLAN §5.4).

Pipeline per upload, run in a background thread (single-worker app):
    validate → parsing (PDF → canonical Markdown) → chunking
             → embedding (BGE-M3 or mock) → stored (Qdrant upsert)

Stage/progress/error are written to the manifest after each step so the UI
can poll at 1–2 s. The extracted Markdown is kept on the uploads volume
(``{doc_id}.md``) for inspection/validation, and the original PDF
(``{doc_id}.pdf``) is served back through ``GET /{doc_id}/file`` so the UI
can open it (e.g. a retrieved chunk's source file → original document).
"""
from __future__ import annotations

import re
import threading
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from .. import state, store
from ..config import env
from ..pipeline.chunking import chunk_markdown
from ..pipeline.embedding import embed
from ..pipeline.pdf import NoTextLayerError, extract_markdown
from ..schemas import DocumentOut, UploadOut

router = APIRouter(prefix="/documents", tags=["documents"])

PDF_MAGIC = b"%PDF-"
CHUNK = 1024 * 1024  # read uploads in 1 MB pieces so the limit is enforced early


def _uploads_dir() -> Path:
    d = Path(env.uploads_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


@router.post("", response_model=UploadOut)
async def upload_document(file: UploadFile = File(...)):
    filename = Path(file.filename or "onbekend.pdf").name
    max_bytes = int(env.upload_max_mb) * 1024 * 1024

    parts: list[bytes] = []
    size = 0
    while part := await file.read(CHUNK):
        parts.append(part)
        size += len(part)
        if size > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Bestand is te groot (maximaal {env.upload_max_mb} MB).",
            )
    data = b"".join(parts)

    if not data.startswith(PDF_MAGIC):
        raise HTTPException(status_code=415, detail="Dit is geen geldig PDF-bestand.")

    doc_id = uuid.uuid4().hex
    (_uploads_dir() / f"{doc_id}.pdf").write_bytes(data)

    state.create(doc_id, filename)
    threading.Thread(target=_ingest, args=(doc_id, filename), daemon=True).start()
    return UploadOut(doc_id=doc_id, filename=filename, status="uploaded")


@router.get("", response_model=list[DocumentOut])
def list_documents():
    return [DocumentOut(**entry) for entry in state.list_all()]


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: str):
    entry = state.get(doc_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Document niet gevonden.")
    return DocumentOut(**entry)


@router.get("/{doc_id}/file")
def get_document_file(doc_id: str):
    """Serve the original uploaded PDF.

    ``Content-Disposition: inline`` so the browser's own PDF viewer shows it
    (open in a new tab from the UI). The original file is kept on the
    uploads volume per document (PLAN v1.1: retrieved chunks link back to
    their source file).
    """
    if not re.fullmatch(r"[0-9a-f]{32}", doc_id):
        raise HTTPException(status_code=400, detail="Ongeldig document-id.")
    entry = state.get(doc_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Document niet gevonden.")
    p = _uploads_dir() / f"{doc_id}.pdf"
    if not p.exists():
        raise HTTPException(status_code=410, detail="Het originele bestand is niet (meer) beschikbaar.")
    return FileResponse(
        p,
        media_type="application/pdf",
        filename=entry["filename"],
        content_disposition_type="inline",
    )


@router.delete("/{doc_id}")
def delete_document(doc_id: str):
    entry = state.get(doc_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Document niet gevonden.")
    try:
        store.delete_by_doc(doc_id)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Vectors konden niet worden verwijderd: {e}"
        ) from e
    d = _uploads_dir()
    for suffix in (".pdf", ".md"):
        p = d / f"{doc_id}{suffix}"
        if p.exists():
            p.unlink()
    state.remove(doc_id)
    return {"ok": True, "doc_id": doc_id}


# ── background ingestion ──────────────────────────────────────────────────────


def _ingest(doc_id: str, filename: str) -> None:
    d = _uploads_dir()
    pdf_path = d / f"{doc_id}.pdf"
    md_path = d / f"{doc_id}.md"
    title = Path(filename).stem

    try:
        # 1. parsing — PDF → canonical Markdown (stored for inspection)
        state.update(doc_id, status="parsing", stage="parsing", progress=5)
        markdown = extract_markdown(pdf_path, source_name=filename, title=title)
        md_path.write_text(markdown, encoding="utf-8")
        state.update(doc_id, progress=20)

        # 2. chunking — structure-aware, 256–512 tokens, ~15 % overlap
        state.update(doc_id, status="chunking", stage="chunking", progress=30)
        chunks = chunk_markdown(markdown, doc_id)
        if not chunks:
            raise RuntimeError("Geen chunks kunnen worden gegenereerd uit de tekstlaag.")

        # 3. embedding — BGE-M3 (or mock) in batches of 16
        state.update(doc_id, status="embedding", stage="embedding", progress=35)
        total = len(chunks)

        def _progress(done: int, n: int) -> None:
            state.update(doc_id, progress=35 + int(done / max(n, 1) * 55))

        vectors = embed([c.chunk_markdown for c in chunks], on_progress=_progress)

        # 4. stored — Qdrant upsert (cosine), manifest done
        payload_chunks = [
            {
                "chunk_id": c.chunk_id,
                "source": filename,
                "title": title,
                "type": "pdf",
                "page": c.page,
                "chunk_index": c.chunk_index,
                "language": "nl",
                "chunk_markdown": c.chunk_markdown,
            }
            for c in chunks
        ]
        store.upsert_chunks(doc_id, payload_chunks, vectors)
        state.update(
            doc_id,
            status="stored",
            stage="stored",
            progress=100,
            chunks=len(chunks),
            error=None,
        )
    except NoTextLayerError as e:
        state.update(doc_id, status="error", stage="error", progress=0, error=str(e))
    except Exception as e:
        state.update(
            doc_id, status="error", stage="error", progress=0, error=f"{type(e).__name__}: {e}"
        )
