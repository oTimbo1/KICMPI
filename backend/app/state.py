"""Document manifest (``docs.json``) on the uploads volume.

Holds per-document pipeline state so the UI can poll live progress:

    status ∈ uploaded | parsing | chunking | embedding | stored | error

Single-writer by design: ingestion runs in one background thread per upload,
all mutations happen under a lock.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .config import env

_lock = threading.Lock()


def _path() -> Path:
    return Path(env.uploads_dir) / "docs.json"


def _ensure_dir() -> None:
    Path(env.uploads_dir).mkdir(parents=True, exist_ok=True)


def _read() -> dict[str, dict[str, Any]]:
    p = _path()
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write(docs: dict[str, dict[str, Any]]) -> None:
    _ensure_dir()
    tmp = _path().with_name("docs.json.tmp")
    tmp.write_text(json.dumps(docs, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(_path())


def create(doc_id: str, filename: str) -> dict[str, Any]:
    entry = {
        "doc_id": doc_id,
        "filename": filename,
        "uploaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "uploaded",
        "stage": "uploaded",
        "progress": 0,
        "chunks": 0,
        "error": None,
    }
    with _lock:
        docs = _read()
        docs[doc_id] = entry
        _write(docs)
    return entry


def get(doc_id: str) -> Optional[dict[str, Any]]:
    with _lock:
        return _read().get(doc_id)


def update(doc_id: str, **fields: Any) -> None:
    with _lock:
        docs = _read()
        if doc_id not in docs:
            return
        docs[doc_id].update(fields)
        _write(docs)


def remove(doc_id: str) -> bool:
    with _lock:
        docs = _read()
        if docs.pop(doc_id, None) is None:
            return False
        _write(docs)
        return True


def list_all() -> list[dict[str, Any]]:
    with _lock:
        docs = _read()
    return sorted(docs.values(), key=lambda d: d.get("uploaded_at", ""), reverse=True)
