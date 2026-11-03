#!/usr/bin/env python3
"""
Minimal HTTP wrapper around whisper.cpp — KicMPi RAG project.

whisper.cpp is a CLI (sister project of llama.cpp, same GGUF format) and has
no HTTP server of its own. The KicMPi web app must reach *every* model via
IP:port, so this thin wrapper exposes whisper-large-v3 as a small HTTP
service (OpenAI-style surface, so the app's status probe works uniformly).

Endpoints
---------
GET  /v1/models       → health/status probe: {"data": [{"id": "whisper-large-v3", ...}]}
POST /v1/transcribe   → multipart upload:
                           file : audio (16 kHz mono WAV recommended — the pipeline's
                                  FFmpeg step prepares it; mp3/flac work if whisper.cpp
                                  was built with ffmpeg support)
                           lang : language code, default "nl" (Dutch-first corpus),
                                  "auto" to let whisper decide
                           fmt  : "srt" (default) or "json"
                         → {"srt": "...", "language": "nl", "took_s": 12.3}
                         or {"segments": [...], "language": "nl", "took_s": 12.3}

Setup
-----
    pip install fastapi uvicorn python-multipart
    export WHISPER_BIN=./whisper.cpp/build/bin/main        # or your build path
    export WHISPER_MODEL=/path/to/ggml-large-v3.q8_0.bin
    ./start-whisper.sh                                     # binds 0.0.0.0:8083

Notes
-----
- One transcription at a time (single worker). Fine for batch ingestion.
- For very long videos, chunk the audio before calling (pipeline concern, not wrapper's).
"""

import json
import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

WHISPER_BIN = os.environ.get("WHISPER_BIN", "./whisper.cpp/build/bin/main")
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "/path/to/ggml-large-v3.q8_0.bin")
DEFAULT_LANG = os.environ.get("WHISPER_LANG", "nl")
TIMEOUT_S = int(os.environ.get("WHISPER_TIMEOUT_S", "3600"))

app = FastAPI(title="whisper.cpp server (KicMPi RAG)")


@app.get("/v1/models")
def models():
    """Status probe used by the web app's Settings tab / status panel."""
    return {"object": "list", "data": [{"id": "whisper-large-v3", "object": "model"}]}


@app.post("/v1/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    lang: str = Form(DEFAULT_LANG),
    fmt: str = Form("srt"),
):
    if not Path(WHISPER_MODEL).is_file():
        raise HTTPException(status_code=503, detail="Whisper model file not found — set WHISPER_MODEL.")
    if not Path(WHISPER_BIN).is_file():
        raise HTTPException(status_code=503, detail="whisper.cpp binary not found — set WHISPER_BIN.")

    workdir = Path(tempfile.mkdtemp(prefix="kicmpi-asr-"))
    in_path = workdir / f"audio-{uuid.uuid4().hex[:8]}.wav"
    in_path.write_bytes(await file.read())

    out_base = workdir / "out"
    cmd = [
        WHISPER_BIN,
        "-m", WHISPER_MODEL,
        "-l", lang,
        "-f", str(in_path),
        "-of", str(out_base),
    ]
    cmd.append("-oj" if fmt == "json" else "-osrt")

    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="whisper.cpp timed out.")
    finally:
        await file.close()

    if proc.returncode != 0:
        raise HTTPException(status_code=500, detail=f"whisper.cpp failed: {proc.stderr[-500:]}")

    took = round(time.time() - t0, 1)
    if fmt == "json":
        data = json.loads((out_base.with_suffix(".json")).read_text(encoding="utf-8"))
        return {"segments": data.get("transcription", []), "language": lang, "took_s": took}

    srt_path = out_base.with_suffix(".srt")
    srt = srt_path.read_text(encoding="utf-8") if srt_path.exists() else ""
    return {"srt": srt, "language": lang, "took_s": took}
