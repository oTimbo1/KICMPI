"""Qdrant access: collection lifecycle, upsert, search, delete.

The collection is created on first use (cosine, ``EMBED_DIMS``) with payload
indexes on ``doc_id`` / ``type`` / ``page`` (PLAN §5.4 step 5).

Point ids are the UUID encoding of ``chunk_id = sha256(doc_id:chunk_index)``
— Qdrant requires UUID/uint point ids, so the same deterministic id is stored
as a string in the payload for API use.
"""
from __future__ import annotations

import uuid
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    VectorParams,
)

from .config import env, settings

_client: Optional[QdrantClient] = None


def _point_id(chunk_id: str) -> "uuid.UUID":
    """Qdrant point ids are 128-bit UUIDs; ``chunk_id`` is a 256-bit sha256 hex.

    The first 128 bits are used as the point id (collision negligible at our
    corpus size); the full sha256 stays in the payload as ``chunk_id``.
    """
    return uuid.UUID(hex=chunk_id[:32])


def client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=env.qdrant_url, timeout=30)
    return _client


def collection() -> str:
    return env.qdrant_collection


def dims() -> int:
    return int(settings.get("embed_dims"))


def ensure_collection() -> str:
    """Create the collection + payload indexes on first use."""
    c = client()
    name = collection()
    if not c.collection_exists(name):
        c.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=dims(), distance=Distance.COSINE),
        )
        c.create_payload_index(collection_name=name, field_name="doc_id", field_schema="keyword")
        c.create_payload_index(collection_name=name, field_name="type", field_schema="keyword")
        c.create_payload_index(collection_name=name, field_name="page", field_schema="integer")
    return name


def upsert_chunks(doc_id: str, chunks: list[dict], vectors: list[list[float]]) -> None:
    """chunks: [{chunk_id, source, title, type, page, chunk_index, language, chunk_markdown}]"""
    ensure_collection()
    points = []
    for ch, vec in zip(chunks, vectors):
        payload = {
            "chunk_id": ch["chunk_id"],
            "doc_id": doc_id,
            "source": ch["source"],
            "title": ch["title"],
            "type": ch["type"],
            "page": ch["page"],
            "chunk_index": ch["chunk_index"],
            "language": ch["language"],
            "chunk_markdown": ch["chunk_markdown"],
        }
        points.append(PointStruct(id=_point_id(ch["chunk_id"]), vector=vec, payload=payload))
    c = client()
    batch = 64
    for i in range(0, len(points), batch):
        c.upsert(collection_name=collection(), points=points[i : i + batch], wait=True)


def search(
    query_vector: list[float], top_k: int, doc_id: Optional[str] = None
) -> list:
    """Top-k cosine search; optional doc filter. Returns ScoredPoint list."""
    ensure_collection()
    query_filter = None
    if doc_id:
        query_filter = Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        )
    res = client().query_points(
        collection_name=collection(),
        query=query_vector,
        limit=top_k,
        query_filter=query_filter,
    )
    return res.points


def delete_by_doc(doc_id: str) -> None:
    c = client()
    if not c.collection_exists(collection()):
        return
    c.delete(
        collection_name=collection(),
        points_selector=FilterSelector(
            filter=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            )
        ),
    )


def count() -> int:
    if not client().collection_exists(collection()):
        return 0
    return client().count(collection_name=collection(), exact=True).count
