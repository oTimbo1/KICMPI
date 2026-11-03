#!/bin/bash
#
# Qwen3-VL-8B-Instruct vision server (llama.cpp + mmproj) — KicMPi RAG project
#   Role:     image-to-text converter of the full pipeline: PDF pages + sampled video
#             frames → Markdown (OCR + layout/figure descriptions), via
#             POST /v1/chat/completions with image input (OpenAI-compatible)
#   Source:   https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct-GGUF
#             (model Q4_K_M + mmproj Q8_0, f16 fallback)
#   Endpoint: http://<this-system-ip>:8084
#   Needed:   v1 (NO — v1 uses the text-layer PDF path) / full pipeline (yes)
#   Port:     8084 (8082 is used by the Qwen3-8B summary server)
#
cd "$(dirname "$0")"

LLAMA_SERVER="${LLAMA_SERVER:-./llama.cpp/build/bin/llama-server}"
MODEL="${MODEL:-/path/to/Qwen3-VL-8B-Instruct-GGUF/Qwen3-VL-8B-Instruct-Q4_K_M.gguf}"   # ← adjust
MMPROJ="${MMPROJ:-/path/to/Qwen3-VL-8B-Instruct-GGUF/mmproj-Q8_0.gguf}"                 # ← adjust
PORT=8084

while true; do
    echo
    echo "Starting Qwen3-VL-8B vision server on 0.0.0.0:${PORT} ..."

    "$LLAMA_SERVER" \
      --alias "qwen3-vl-8b" \
      --batch-size 2048 \
      --cache-type-k q8_0 \
      --cache-type-v q8_0 \
      --ctx-size 16384 \
      --flash-attn on \
      --host 0.0.0.0 \
      --jinja \
      --mmproj "$MMPROJ" \
      --model "$MODEL" \
      --n-gpu-layers all \
      --parallel 1 \
      --port "$PORT" \
      --ubatch-size 2048 \
      --verbosity 2

    echo
    echo "Qwen3-VL server stopped or crashed."

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
