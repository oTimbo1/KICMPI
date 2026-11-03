"""KicMPi RAG concept web app — FastAPI backend (PLAN_WEBAPP_V1.md §5).

Run (inside Docker): uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import env
from .routers import documents, search, settings as settings_router, status


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Make sure the data volumes exist (they are created by Docker anyway).
    Path(env.uploads_dir).mkdir(parents=True, exist_ok=True)
    Path(env.config_dir).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="KicMPi RAG — concept web app",
    version="0.1.0",
    description="PDF → Markdown → chunks → BGE-M3 → Qdrant → search + grounded summary",
    lifespan=lifespan,
)

# Same-origin through nginx in production; CORS kept for the Vite dev server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(status.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"ok": True, "app": "kicmpi-rag", "version": "0.1.0"}
