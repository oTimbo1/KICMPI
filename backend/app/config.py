"""App configuration: environment defaults + runtime overrides.

Two layers (see PLAN_WEBAPP_V1.md §3.1 / §5.1):
  1. **env defaults** — from the process environment (docker compose / .env).
  2. **runtime overrides** — set through the app's Settings tab, persisted to
     ``{CONFIG_DIR}/settings.json`` on the `config` Docker volume, effective
     immediately (no restart). ``None`` on PUT resets a key to its env default.

Precedence: settings.json > environment.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvDefaults(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # app / network
    app_port: int = 8090
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "kicmpi_documents"

    # model endpoints (defaults — overridable at runtime via Settings tab)
    # 🔒 Port 8080 on the model system is reserved (agent server) — never use it.
    embedding_base_url: str = "http://192.168.69.20:8081"
    embedding_model: str = "bge-m3"
    embed_dims: int = 1024
    summary_base_url: str = "http://192.168.69.20:8082"
    summary_model: str = "qwen3-8b"
    # Reserved for the full pipeline (later sprints) — stored, unused in v1
    vlm_base_url: str = "http://192.168.69.20:8084"
    vlm_model: str = "qwen3-vl-8b-instruct"
    asr_base_url: str = "http://192.168.69.20:8083"
    asr_model: str = "whisper-large-v3"

    # behaviour
    embed_mock: bool = False
    upload_max_mb: int = 25

    # local paths (Docker volumes)
    uploads_dir: str = "/data/uploads"
    config_dir: str = "/data/config"


env = EnvDefaults()

#: Keys that may be overridden at runtime (Settings tab → settings.json)
OVERRIDABLE: tuple[str, ...] = (
    "embedding_base_url",
    "embedding_model",
    "summary_base_url",
    "summary_model",
    "vlm_base_url",
    "vlm_model",
    "asr_base_url",
    "asr_model",
    "embed_mock",
)


class SettingsStore:
    """Runtime overrides, persisted to ``{CONFIG_DIR}/settings.json``."""

    def __init__(self, path: Path):
        self._path = path
        self._lock = threading.Lock()
        self._overrides: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._overrides = {k: v for k, v in data.items() if k in OVERRIDABLE}
            except Exception:
                self._overrides = {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_name(self._path.name + ".tmp")
        tmp.write_text(json.dumps(self._overrides, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._path)

    def get(self, key: str) -> Any:
        """Effective value: override if present, else the env default."""
        with self._lock:
            if key in self._overrides:
                return self._overrides[key]
            return getattr(env, key)

    def update(self, patch: dict[str, Any]) -> None:
        """Apply a partial update (None = reset to env default) and persist."""
        with self._lock:
            changed = False
            for key, value in patch.items():
                if key not in OVERRIDABLE:
                    continue
                if value is None:
                    if key in self._overrides:
                        self._overrides.pop(key)
                        changed = True
                elif self._overrides.get(key) != value:
                    self._overrides[key] = value
                    changed = True
            if changed:
                self._save()


settings = SettingsStore(Path(env.config_dir) / "settings.json")


def effective() -> dict[str, Any]:
    """All effective settings (overrides on top of env defaults)."""
    return {key: settings.get(key) for key in OVERRIDABLE}


def norm_url(url: str | None) -> str:
    """Normalise a user-entered endpoint URL (Settings tab is a UI-only surface,
    so be forgiving about pasted paths like ``…/v1/models``)."""
    url = (url or "").strip().rstrip("/")
    for suffix in ("/v1/models", "/v1/embeddings", "/v1/chat/completions", "/v1"):
        if url.endswith(suffix):
            return url[: -len(suffix)]
    return url
