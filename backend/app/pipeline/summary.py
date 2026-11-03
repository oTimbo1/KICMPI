"""Grounded summary via the summary LLM (Qwen3-8B on llama.cpp) — PLAN §5.5.

Best-effort by design: any failure yields ``status: "error: …"`` (or
``"unconfigured"``) and **never blocks chunk retrieval** (PLAN §5.2).

System prompt (Dutch, per TOOLING_SELECTION_AND_PIPELINE.md §3.7): answer only
from the provided chunks, be concise, cite each claim as [bron, pagina], and
abstain explicitly when the chunks do not contain the answer.

Qwen3 is a "thinking" model; ``chat_template_kwargs.enable_thinking = false``
is sent (ignored by non-Qwen3 llama.cpp servers) so the demo gets short, fast,
grounded answers instead of burning max_tokens on hidden reasoning.
"""
from __future__ import annotations

from typing import Any

import httpx

from ..config import settings

SYSTEM_PROMPT = (
    "Beantwoord de vraag uitsluitend op basis van de meegegeven chunks. "
    "Wees beknopt (2-5 zinnen). Vermeld bij elke bewering de bron in de vorm "
    "[bestandsnaam, p. N] — gebruik de bestandsnaam en het paginanummer die bij "
    "de chunk staan vermeld. Als de chunks het antwoord niet bevatten, zeg dan "
    "expliciet dat er in het corpus geen antwoord gevonden is."
)

TIMEOUT_S = 60.0
MAX_TOKENS = 400
TEMPERATURE = 0.2

NO_CHUNKS_ANSWER = (
    "In het corpus zijn geen relevante chunks gevonden voor deze vraag, "
    "dus er is geen antwoord beschikbaar."
)


def _base_url() -> str:
    return str(settings.get("summary_base_url") or "").rstrip("/")


def _model() -> str:
    return str(settings.get("summary_model") or "")


def _user_message(query: str, chunks: list[dict[str, Any]]) -> str:
    lines = [f"Vraag: {query}", "", "Chunks:"]
    for i, ch in enumerate(chunks, start=1):
        page = ch.get("page")
        where = f"pagina {page}" if page else "zonder paginanummer"
        lines.append(f"[{i}] Bron: {ch.get('source', 'onbekend')}, {where}")
        lines.append(str(ch.get("chunk_markdown", "")).strip())
        lines.append("")
    return "\n".join(lines)


def summarize(query: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Return ``{"status": "ok|unconfigured|error:<msg>", "model": str|None, "text": str|None}``.

    ``text`` is non-null only when ``status == "ok"``.
    """
    base = _base_url()
    model = _model()
    if not base or not model:
        return {"status": "unconfigured", "model": None, "text": None}
    if not chunks:
        return {"status": "ok", "model": model, "text": NO_CHUNKS_ANSWER}

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _user_message(query, chunks)},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    try:
        with httpx.Client(timeout=TIMEOUT_S) as http:
            resp = http.post(f"{base}/v1/chat/completions", json=body)
            resp.raise_for_status()
            data = resp.json()
        text = (data["choices"][0]["message"].get("content") or "").strip()
        if not text:
            return {"status": "error: leeg antwoord van het model", "model": model, "text": None}
        return {"status": "ok", "model": model, "text": text}
    except httpx.HTTPError as e:
        return {
            "status": f"error: samenvatting-model niet bereikbaar ({type(e).__name__})",
            "model": model,
            "text": None,
        }
    except Exception as e:  # defensive: never break the search response
        return {"status": f"error: {type(e).__name__}: {e}", "model": model, "text": None}
