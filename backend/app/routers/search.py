"""Search: query embedding → Qdrant top-k → chunks + best-effort summary.

Chunk retrieval succeeds independently of the summary model (PLAN §5.2):
summary failures surface as ``summary.status = "error: …"`` while the chunks
are still returned.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException

from .. import store
from ..pipeline.embedding import embed
from ..pipeline.summary import summarize
from ..schemas import ChunkOut, SearchRequest, SearchResponse, SummaryOut

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search(body: SearchRequest):
    started = time.time()

    # 1. embed the query (same endpoint/model as the corpus)
    try:
        query_vector = embed([body.query.strip()])[0]
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    # 2. retrieve top-k (optional document filter)
    try:
        points = store.search(query_vector, top_k=body.top_k, doc_id=body.doc_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Qdrant-zoeken mislukt: {e}") from e

    chunks = [
        ChunkOut(
            chunk_id=str(p.payload.get("chunk_id", "")),
            doc_id=str(p.payload.get("doc_id", "")),
            source=str(p.payload.get("source", "")),
            title=str(p.payload.get("title", "")),
            page=int(p.payload.get("page", 0)),
            score=round(float(p.score), 4),
            text=str(p.payload.get("chunk_markdown", "")),
        )
        for p in points
    ]

    # 3. grounded summary — best effort, never blocks the chunks
    summary = summarize(body.query, [c.model_dump() for c in chunks])

    return SearchResponse(
        query=body.query,
        chunks=chunks,
        summary=SummaryOut(**summary),
        took_ms=int((time.time() - started) * 1000),
    )
