"""Settings: model endpoints in the UI (PLAN §3.1 / §5.1 / View 3).

``GET  /settings`` — current effective settings (overrides on top of env).
``PUT  /settings`` — partial update; persisted to ``settings.json`` on the
``config`` volume and effective immediately (no restart). ``None`` resets a
key to its environment default. VLM/ASR endpoints are stored now (reserved
for the full pipeline) but unused in v1.
"""
from __future__ import annotations

from fastapi import APIRouter

from ..config import effective, norm_url, settings
from ..schemas import SettingsOut, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])

#: API field name → settings-store key
_KEY_MAP = {
    "embedding_url": "embedding_base_url",
    "embedding_model": "embedding_model",
    "summary_url": "summary_base_url",
    "summary_model": "summary_model",
    "vlm_url": "vlm_base_url",
    "vlm_model": "vlm_model",
    "asr_url": "asr_base_url",
    "asr_model": "asr_model",
    "embed_mock": "embed_mock",
    "qdrant_dashboard_url": "qdrant_dashboard_url",
}

_URL_FIELDS = ("embedding_url", "summary_url", "vlm_url", "asr_url", "qdrant_dashboard_url")


def _to_out(eff: dict) -> SettingsOut:
    return SettingsOut(
        embedding_url=eff["embedding_base_url"],
        embedding_model=eff["embedding_model"],
        summary_url=eff["summary_base_url"],
        summary_model=eff["summary_model"],
        vlm_url=eff["vlm_base_url"],
        vlm_model=eff["vlm_model"],
        asr_url=eff["asr_base_url"],
        asr_model=eff["asr_model"],
        embed_mock=bool(eff["embed_mock"]),
        qdrant_dashboard_url=str(eff["qdrant_dashboard_url"] or ""),
    )


@router.get("", response_model=SettingsOut)
def get_settings():
    return _to_out(effective())


@router.put("", response_model=SettingsOut)
def put_settings(body: SettingsUpdate):
    raw = body.model_dump()
    for key in _URL_FIELDS:
        if raw.get(key) is not None:
            raw[key] = norm_url(raw[key])
    # empty strings mean "not set" → reset to env default
    for key in list(raw):
        if isinstance(raw[key], str) and not raw[key].strip():
            raw[key] = None
    patch = {_KEY_MAP[k]: v for k, v in raw.items() if k in _KEY_MAP}
    settings.update(patch)
    return _to_out(effective())
