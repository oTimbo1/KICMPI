#!/bin/bash
#
# whisper.cpp HTTP wrapper (NOT llama.cpp — sister project, same GGUF format)
#   Role:     audio-to-text converter of the full pipeline: video audio / MP3
#             → timestamped SRT (→ Markdown by the web app backend)
#   Source:   https://huggingface.co/ggerganov/whisper.cpp/tree/main/models
#             (ggml-large-v3.q8_0.bin recommended; f16 ggml-large-v3.bin for max accuracy)
#   Endpoint: http://<this-system-ip>:8083  →  POST /v1/transcribe, GET /v1/models
#   Needed:   v1 demo (NO) / full pipeline (yes)
#   Extra:    pip install fastapi uvicorn python-multipart
#
cd "$(dirname "$0")"

export WHISPER_BIN="${WHISPER_BIN:-./whisper.cpp/build/bin/main}"
export WHISPER_MODEL="${WHISPER_MODEL:-/path/to/whisper-large-v3/ggml-large-v3.q8_0.bin}"   # ← adjust
export WHISPER_LANG="${WHISPER_LANG:-nl}"
HOST=0.0.0.0
PORT=8083

while true; do
    echo
    echo "Starting whisper.cpp wrapper on ${HOST}:${PORT} ..."

    python3 -m uvicorn whisper_server:app --host "$HOST" --port "$PORT"

    echo
    echo "whisper.cpp wrapper stopped or crashed."

    read -t 5 -p "Terminate script entirely? (y/N): " choice
    choice=${choice:-n}

    if [[ "$choice" =~ ^[Yy]$ ]]; then
        echo "Exiting script."
        break
    else
        echo "Restarting server in 2 seconds..."
        sleep 2
    fi
done
