# Model servers — prep guide (model system)

> For the **KicMPi RAG project**. This folder contains everything needed to run the model servers on the project's model system (a GPU machine on the same LAN as the app host). Copy the whole `model-servers/` folder there, point each script at its model file (`MODEL` env var — see §3 for the suggested layout), and start what you need.
>
> The KicMPi web app (Docker, on the app host) reaches these servers **only via IP:port** — entered once in the app's **Settings tab** (or via `.env`). Nothing in the web app knows or depends on the model system otherwise.

## 1. The four models (all from Hugging Face, all GGUF)

| # | Model | Role | Runtime | HF source | Recommended file(s) | ≈ Size | Port |
|---|---|---|---|---|---|---|---|
| 1 | **BGE-M3** | Embedding (chunks + queries → 1024-dim vectors) | llama.cpp (`llama-server --embedding`) | [`lm-kit/bge-m3-gguf`](https://huggingface.co/lm-kit/bge-m3-gguf) | `bge-m3-F16.gguf` (or `bge-m3-Q8_0.gguf`) | ≈1.1 GB | **8081** |
| 2 | **Qwen3-8B** | Summary LLM (grounded NL answer from chunks) | llama.cpp (`llama-server`) | [`Qwen/Qwen3-8B-GGUF`](https://huggingface.co/Qwen/Qwen3-8B-GGUF) | `Qwen3-8B-Q4_K_M.gguf` (≈5 GB) | ≈5–6 GB | **8082** ⚑ |
| 3 | **Qwen3-VL-8B-Instruct** | Image-to-text: PDF pages + video frames → Markdown | llama.cpp (`llama-server --mmproj`) | [`Qwen/Qwen3-VL-8B-Instruct-GGUF`](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct-GGUF) | model `Q4_K_M` + **mmproj** `Q8_0` (f16 fallback) | ≈6–8 GB incl. mmproj | **8084** |
| 4 | **whisper-large-v3** | Audio-to-text: video audio + MP3 → timestamped SRT | **whisper.cpp** (sister project of llama.cpp — same GGUF format, *different binary*; it has no HTTP server, hence the small wrapper here) | [`ggerganov/whisper.cpp` → `models/`](https://huggingface.co/ggerganov/whisper.cpp/tree/main/models) | `ggml-large-v3.q8_0.bin` (f16 `ggml-large-v3.bin` for max accuracy) | ≈1.6 GB (q8) — CPU is fine | **8083** |

> ⚑ **Port note (2026-11-02, model system `192.168.69.20`):** 🔒 **port 8080 is RESERVED there** (pre-existing non-RAG service) and must **never** be used by the RAG system or any of its scripts/defaults. Actual layout: 8080 = reserved, 8081 = BGE-M3, 8082 = Qwen3-8B, 8083 = whisper (later), 8084 = VLM (later). BGE-M3 + Qwen3-8B were **up and verified reachable** (2026-11-02).

**For v1 you only need #1 + #2.** #3 and #4 are for the full pipeline (video/audio ingestion) in a later sprint — set them up now if you like, but they are not v1 blockers.

## 2. VRAM budget (one GPU, all four running)

| Model | Quat | ≈ VRAM |
|---|---|---|
| BGE-M3 | f16 | ≈1.2 GB |
| Qwen3-8B | Q4_K_M | ≈5–6 GB |
| Qwen3-VL-8B | Q4_K_M + mmproj Q8_0 | ≈6–8 GB |
| whisper-large-v3 | q8_0 | ≈1.6 GB (or 0 — runs fine on CPU) |
| **Total** | | **≈13–16 GB** |

- **24 GB card:** comfortable with all four.
- **16 GB card:** workable — run whisper on CPU (add `-t <n-cpu-threads>` to the whisper call in `whisper_server.py`) and remember the VLM is only needed during batch ingestion, not at query time (tooling doc §3.9: VLM and summary LLM rarely overlap).
- v1 minimum (BGE-M3 + Qwen3-8B): ≈7 GB.

## 3. Download the models

Suggested layout (adjust to your machine):

```
~/AI/models/
├── bge-m3/bge-m3-F16.gguf                            # ✅ downloaded 2026-11-02
├── Qwen3-8B/Qwen3-8B-Q4_K_M.gguf                     # ✅ downloaded 2026-11-02
├── Qwen3-VL-8B-Instruct-GGUF/                        # (later sprint)
│   ├── Qwen3-VL-8B-Instruct-Q4_K_M.gguf
│   └── mmproj-Q8_0.gguf          # ← the vision projector, same repo
└── whisper-large-v3/ggml-large-v3.q8_0.bin           # (later sprint)
```

e.g. with `huggingface-cli`:

```bash
huggingface-cli download lm-kit/bge-m3-gguf bge-m3-F16.gguf --local-dir ~/AI/models/bge-m3
huggingface-cli download Qwen/Qwen3-8B-GGUF Qwen3-8B-Q4_K_M.gguf --local-dir ~/AI/models/Qwen3-8B
huggingface-cli download Qwen/Qwen3-VL-8B-Instruct-GGUF Qwen3-VL-8B-Instruct-Q4_K_M.gguf mmproj-Q8_0.gguf --local-dir ~/AI/models/Qwen3-VL-8B-Instruct-GGUF
huggingface-cli download ggerganov/whisper.cpp ggml-large-v3.q8_0.bin --local-dir ~/AI/models/whisper-large-v3
```

(Exact file names may differ slightly per repo revision — pick the matching quant in the repo file list; the scripts only care about the path you set.)

## 4. Start the servers

Each script uses a simple restart loop (crash → "terminate or restart in 2 s"), binds **`0.0.0.0`** so the app host on the LAN can reach them, and assumes `llama.cpp` (and for whisper, the `whisper.cpp` build) is checked out next to the scripts — adjust `LLAMA_SERVER` / `WHISPER_BIN` at the top of each script if your build lives elsewhere.

```bash
chmod +x start-*.sh

# v1 (required):
MODEL=~/AI/models/bge-m3/bge-m3-F16.gguf ./start-bge-m3.sh      # embedding → http://<this-ip>:8081
MODEL=~/AI/models/Qwen3-8B/Qwen3-8B-Q4_K_M.gguf ./start-qwen3-8b.sh   # summary   → http://<this-ip>:8082

# full pipeline (later sprint):
./start-qwen3-vl.sh    # image-text → http://<this-ip>:8084
./start-whisper.sh     # audio-text → http://<this-ip>:8083   (needs: pip install fastapi uvicorn python-multipart)
```

Run each in its own terminal/tmux pane (or `nohup ... &`).

> ⚠️ **BGE-M3 `--batch-size` (2026-11-03, found during integration):** the physical batch
> must be able to fit a single long input. The web app's Markdown chunks target ≤ ~500
> tokens; with the old default of `512` llama.cpp returned `HTTP 500 — input is too large
> to process` for longer chunks. The script now sets **`--batch-size 8192`** (with
> `--ubatch-size 512` unchanged). **If the embedding server is currently running with the
> old value, restart it with this script** — or leave it: the web app defensively
> segment-averages any input > 400 words, so it works either way (8192 is just cleaner).

## 5. Verify (from the app host, or any LAN machine)

```bash
curl http://<model-ip>:8081/v1/models    # BGE-M3     → expect {"data":[{"id":"bge-m3",...}]}
curl http://<model-ip>:8082/v1/models    # Qwen3-8B   → expect {"data":[{"id":"qwen3-8b",...}]}
curl http://<model-ip>:8084/v1/models    # Qwen3-VL   → expect {"data":[{"id":"qwen3-vl-8b",...}]}
curl http://<model-ip>:8083/v1/models    # whisper    → expect {"data":[{"id":"whisper-large-v3",...}]}
```

The web app's **Settings tab** ("Test verbinding" per model) runs exactly these probes and shows green/red in the UI — so the same check is one click in the app.

## 6. Notes & gotchas

- **whisper.cpp is not llama.cpp.** The "GGUF everywhere" constraint holds at the format/ecosystem level (same ggml family); the two runtimes are named separately everywhere (tooling doc decision log #2). The wrapper (`whisper_server.py`) exists *only* because whisper.cpp is a CLI; it keeps the "all models reachable via IP:port" rule uniform for the web app.
- **Audio to whisper should be 16 kHz mono WAV.** In the full pipeline the web app's backend does the FFmpeg conversion (`ffmpeg -i in.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le out.wav`) before calling the wrapper; the wrapper itself stays thin.
- **Ports by convention:** 8081 embedding / 8082 summary / 8083 whisper / 8084 VLM (8080 is reserved for a pre-existing non-RAG service — do not reuse it). If you must move one, update the value in the app's Settings tab (and optionally `.env`).
- **Firewall:** allow inbound TCP 8081–8084 on the model system for the LAN subnet if the app host sits on another machine.
- **Language:** whisper is started with `-l nl` by default (Dutch-first corpus); pass `?lang=auto` to the wrapper's `/v1/transcribe` if a source turns out to be English.
