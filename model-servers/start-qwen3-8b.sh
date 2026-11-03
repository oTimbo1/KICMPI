#!/bin/bash
#
# Qwen3-8B summary server (llama.cpp) — KicMPi RAG project
#   Role:     generates the short grounded NL answer from retrieved Markdown chunks
#             (Dutch, citations [source, page], abstains when chunks have no answer)
#   Source:   https://huggingface.co/Qwen/Qwen3-8B-GGUF   (Q4_K_M recommended)
#   Endpoint: http://<this-system-ip>:8082  →  POST /v1/chat/completions (OpenAI-compatible)
#   Needed:   v1 (yes) / full pipeline (yes)
#   Port:     8082 (8080 is reserved on the model system — see MODELS.md)
#
cd "$(dirname "$0")"

LLAMA_SERVER="${LLAMA_SERVER:-./llama.cpp/build/bin/llama-server}"
# GGUF path on THIS machine — set via env or adjust the default below
# (suggested layout: see MODELS.md §3).
MODEL="${MODEL:?MODEL not set — e.g. export MODEL=~/AI/models/Qwen3-8B/Qwen3-8B-Q4_K_M.gguf (see MODELS.md §3)}"
PORT=8082

while true; do
    echo
    echo "Starting Qwen3-8B summary server on 0.0.0.0:${PORT} ..."

    "$LLAMA_SERVER" \
      --alias "qwen3-8b" \
      --batch-size 2048 \
      --cache-type-k q8_0 \
      --cache-type-v q8_0 \
      --ctx-size 16384 \
      --flash-attn on \
      --host 0.0.0.0 \
      --jinja \
      --model "$MODEL" \
      --n-gpu-layers all \
      --parallel 1 \
      --port "$PORT" \
      --ubatch-size 2048 \
      --verbosity 2

    echo
    echo "Qwen3-8B server stopped or crashed."

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
