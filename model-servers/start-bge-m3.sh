#!/bin/bash
#
# BGE-M3 embedding server (llama.cpp) — KicMPi RAG project
#   Role:     embeds Markdown chunks + user queries → dense 1024-dim vectors (Qdrant)
#   Source:   https://huggingface.co/lm-kit/bge-m3-gguf   (f16 recommended, q8_0 fallback)
#   Endpoint: http://<this-system-ip>:8081  →  POST /v1/embeddings (OpenAI-compatible)
#   Needed:   v1 demo (yes) / full pipeline (yes)
#
cd "$(dirname "$0")"

LLAMA_SERVER="${LLAMA_SERVER:-./llama.cpp/build/bin/llama-server}"
MODEL="${MODEL:-/home/urnothim-evo-usr/AI/models/bge-m3/bge-m3-F16.gguf}"
PORT=8081

while true; do
    echo
    echo "Starting BGE-M3 embedding server on 0.0.0.0:${PORT} ..."

    "$LLAMA_SERVER" \
      --alias "bge-m3" \
      --embedding \
      # Physical batch must fit our longest single input (a Markdown chunk is
      # ≤ ~500 tokens by design; 8192 leaves headroom). The default of 512
      # makes llama.cpp return HTTP 500 ("input is too large to process") for
      # any longer input — the web app also degrades long inputs defensively,
      # but 8192 is the clean fix.
      --batch-size 8192 \
      --ctx-size 8192 \
      --host 0.0.0.0 \
      --model "$MODEL" \
      --n-gpu-layers all \
      --parallel 1 \
      --port "$PORT" \
      --ubatch-size 512

    echo
    echo "BGE-M3 server stopped or crashed."

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
