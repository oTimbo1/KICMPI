"""Pydantic request/response models for the REST API (all under /api)."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ── Documents ─────────────────────────────────────────────────────────────────

class DocumentOut(BaseModel):
    doc_id: str
    filename: str
    uploaded_at: str  # ISO 8601 (UTC)
    status: str  # uploaded | parsing | chunking | embedding | stored | error
    stage: str
    progress: int = Field(ge=0, le=100)
    chunks: int = 0
    error: Optional[str] = None


class UploadOut(BaseModel):
    doc_id: str
    filename: str
    status: str = "uploaded"


# ── Search ────────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    doc_id: Optional[str] = None


class ChunkOut(BaseModel):
    chunk_id: str
    doc_id: str
    source: str
    title: str
    page: int
    score: float
    text: str


class SummaryOut(BaseModel):
    status: str  # ok | unconfigured | error:<msg>
    model: Optional[str] = None
    text: Optional[str] = None  # only when status == "ok"


class SearchResponse(BaseModel):
    query: str
    chunks: list[ChunkOut]
    summary: SummaryOut
    took_ms: int


# ── Status / probes ───────────────────────────────────────────────────────────

class EndpointStatus(BaseModel):
    ok: bool
    url: str = ""
    latency_ms: Optional[int] = None
    reason: Optional[str] = None


class StatusResponse(BaseModel):
    app: str = "ok"
    mock_mode: bool
    qdrant: EndpointStatus
    embedding: EndpointStatus
    summary: EndpointStatus


class ProbeRequest(BaseModel):
    url: str


class ProbeResult(BaseModel):
    ok: bool
    url: str
    latency_ms: Optional[int] = None
    reason: Optional[str] = None
    models: Optional[list[str]] = None


# ── Settings ──────────────────────────────────────────────────────────────────

class SettingsOut(BaseModel):
    embedding_url: str
    embedding_model: str
    summary_url: str
    summary_model: str
    vlm_url: str
    vlm_model: str
    asr_url: str
    asr_model: str
    embed_mock: bool


class SettingsUpdate(BaseModel):
    """Partial update — omitted/None keys keep (or reset to) their current value.

    ``None`` explicitly resets a key to its environment default.
    """

    embedding_url: Optional[str] = None
    embedding_model: Optional[str] = None
    summary_url: Optional[str] = None
    summary_model: Optional[str] = None
    vlm_url: Optional[str] = None
    vlm_model: Optional[str] = None
    asr_url: Optional[str] = None
    asr_model: Optional[str] = None
    embed_mock: Optional[bool] = None
