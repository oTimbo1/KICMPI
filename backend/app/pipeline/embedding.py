"""Embedding via an OpenAI-compatible endpoint (BGE-M3 on llama.cpp),
or a deterministic mock embedder (``EMBED_MOCK=1``) as an offline development fallback.

The endpoint URL/model come from the effective settings (Settings tab
overrides env), so changes are effective immediately — every call re-reads
them. Batches of 16 texts per request (PLAN §5.4 step 4).

**Adaptive size handling:** llama.cpp rejects a single input longer than its
physical batch (512 tokens on the model system as of 2026-11-03) with
``HTTP 500 "input is too large to process"``. Because the words→tokens ratio
varies with the text (Dutch technical content can run 2+ tokens/word), we
don't guess limits: when the server says "too large", the batch is retried
text-by-text and the offending text is recursively split at a sentence
boundary near the middle, with the segment vectors averaged (L2-normalised)
— a standard long-text embedding fallback. Other errors raise a clear
RuntimeError.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import Callable, Optional

import httpx

from ..config import settings

BATCH_SIZE = 16
TIMEOUT_S = 120.0
MAX_SPLIT_DEPTH = 6

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def mock_mode() -> bool:
    return bool(settings.get("embed_mock"))


def _base_url() -> str:
    return str(settings.get("embedding_base_url") or "").rstrip("/")


def _model() -> str:
    return str(settings.get("embedding_model") or "")


def _mock_vector(text: str) -> list[float]:
    """Deterministic hashed bag-of-words (L2-normalised) at EMBED_DIMS.

    Retrieval degrades to keyword-ish matching — fine for a labelled
    demo fallback, never the deliverable (PLAN §3.1 / §11).
    """
    dims = int(settings.get("embed_dims"))
    vec = [0.0] * dims
    for word in text.lower().split():
        w = "".join(ch for ch in word if ch.isalnum())
        if not w:
            continue
        digest = hashlib.sha256(w.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "big") % dims
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def _average(vecs: list[list[float]]) -> list[float]:
    """Mean of vectors, L2-normalised (long-text embedding fallback)."""
    if len(vecs) == 1:
        return vecs[0]
    acc = list(vecs[0])
    for v in vecs[1:]:
        acc = [a + b for a, b in zip(acc, v)]
    scale = 1.0 / len(vecs)
    acc = [x * scale for x in acc]
    norm = math.sqrt(sum(x * x for x in acc)) or 1.0
    return [x / norm for x in acc]


def _split_near_middle(text: str) -> tuple[str, str]:
    """Split at the sentence boundary closest to the character middle."""
    mid = len(text) // 2
    best: Optional[int] = None
    for m in _SENT_SPLIT.finditer(text):
        if best is None or abs(m.start() - mid) < abs(best - mid):
            best = m.start()
    if best is None or best <= 10 or best >= len(text) - 10:
        return text[:mid], text[mid:]
    return text[:best], text[best:].lstrip()


def _post_batch(
    http: httpx.Client, base: str, model: str, texts: list[str]
) -> Optional[list[list[float]]]:
    """POST one batch. Returns vectors, or None when the server rejected the
    batch because an input is too large (adaptive split path). Other errors
    raise RuntimeError with a clear message."""
    try:
        resp = http.post(
            f"{base}/v1/embeddings",
            json={"model": model, "input": texts},
        )
    except httpx.HTTPError as e:
        raise RuntimeError(f"Embedding-model niet bereikbaar op {base}: {type(e).__name__}") from e
    if resp.status_code == 200:
        data = resp.json().get("data")
        if not data or len(data) != len(texts):
            raise RuntimeError("Embedding-endpoint gaf een onverwacht antwoord (aantal vectoren).")
        return [item["embedding"] for item in data]
    if resp.status_code == 500 and "too large" in resp.text:
        return None  # adaptive: retry per-text / split
    raise RuntimeError(
        f"Embedding-model gaf een fout op {base}: HTTP {resp.status_code} ({resp.text[:120]})"
    )


def _embed_one(
    http: httpx.Client, base: str, model: str, text: str, depth: int = 0
) -> list[float]:
    """Embed a single text, recursively splitting it while the server says
    'too large' (segment vectors are averaged)."""
    vecs = _post_batch(http, base, model, [text])
    if vecs is not None:
        return vecs[0]
    if depth >= MAX_SPLIT_DEPTH:
        raise RuntimeError(
            f"Tekst is te lang voor het embedding-model, ook na opsplitsing ({base})."
        )
    left, right = _split_near_middle(text)
    return _average([
        _embed_one(http, base, model, left, depth + 1),
        _embed_one(http, base, model, right, depth + 1),
    ])


def embed(
    texts: list[str], on_progress: Optional[Callable[[int, int], None]] = None
) -> list[list[float]]:
    """Embed texts → parallel list of vectors.

    Raises RuntimeError with a clear (Dutch-friendly) message when the model
    endpoint is unreachable or misconfigured.
    """
    if not texts:
        return []

    if mock_mode():
        out = [_mock_vector(t) for t in texts]
        if on_progress:
            on_progress(len(texts), len(texts))
        return out

    base = _base_url()
    if not base:
        raise RuntimeError("Geen embedding-URL geconfigureerd — instel via het tab Instellingen.")

    out: list[list[float]] = []
    with httpx.Client(timeout=TIMEOUT_S) as http:
        for start in range(0, len(texts), BATCH_SIZE):
            batch = texts[start : start + BATCH_SIZE]
            vecs = _post_batch(http, base, _model(), batch)
            if vecs is None:
                # batch rejected (some input too large): retry per text,
                # splitting offenders adaptively
                vecs = [_embed_one(http, base, _model(), t) for t in batch]
            out.extend(vecs)
            if on_progress:
                on_progress(min(start + len(batch), len(texts)), len(texts))
    return out
