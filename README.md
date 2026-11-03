# KicMPi RAG System — concept web app

A working concept of a **RAG (Retrieval-Augmented Generation) knowledge assistant for KicMPi**:
upload a PDF → watch it get **parsed → chunked → embedded → stored** in Qdrant → ask a Dutch
query → retrieve chunks **with scores, source and page** → get a grounded **AI summary** with
citations (degrades gracefully when the summary model is not connected).

**Where this project sits:** this repository is the RAG-system component of the KicMPi ×
Data Science project. It is built *alongside* the data science work (the CRISP-DM iterations
documented in the project report) and serves two purposes:

1. **Proof & evaluation base** — a running system that the report's results (retrieval quality,
   chunking/experimentation, evaluation metrics) can point to, and that we keep iterating on
   (tuning, full pipeline, evaluation).
2. **Concept for the client** — a small branded web app (Dutch UI, KicMPi branding) that shows
   how such a knowledge assistant could work inside KicMPi's environment.

It is therefore **not a one-off demo**: expect continuous, mostly data-science-driven
iteration. See `PLAN_WEBAPP_V1.md` (v1 spec + execution log),
`docs/KICMPI_STYLE_GUIDE.md` (branding), and the project root's
`TOOLING_SELECTION_AND_PIPELINE.md` + `SPRINT_PLAN.md` for the wider context.

- **Language:** Dutch UI
- **Stack:** React + Vite + Tailwind (served by nginx) · Python FastAPI · Qdrant — all in Docker
- **Models run OUTSIDE the app** on the project's model system (same LAN): BGE-M3 (embeddings)
  and Qwen3-8B (summaries) behind llama.cpp OpenAI-compatible endpoints, reached **only via
  IP:port** — entered once in the app's **Settings tab**. No model weights in the app, no GPU
  needed on the app host, **data never leaves our own infrastructure** (AVG: an important
  requirement for KicMPi).

---

## 1. Architecture

```
                          APP HOST (Docker)
┌────────────────────────────────────────────────────────────────────────┐
│  Browser (any LAN device) ── http://<host-ip>:8090 ──────────┐         │
│                                                              │         │
│  ┌─────────────── DOCKER COMPOSE (net: kicmpi-rag) ───────────────┐   │
│  │ ┌──────────────┐  /api proxy  ┌──────────────────┐   ┌───────┐ │   │
│  │ │ FRONTEND     │ ───────────► │ BACKEND          │──►│QDRANT │ │   │
│  │ │ nginx:alpine │              │ python:3.12      │   │:6333  │ │   │
│  │ │ + React SPA  │              │ FastAPI :8000    │   │ vol:  │ │   │
│  │ └──────────────┘              │ vol: uploads/    │   │qdrant │ │   │
│  │      :80 (host: 8090)         │ vol: config/     │   └───────┘ │   │
│  └───────────────────────────────┼──────────────────┘             │   │
│                                  │ OpenAI-compatible HTTP         │   │
│            (IP:port — .env defaults or the app's Settings tab)    │   │
└──────────────────────────────────┼─────────────────────────────────┘
        ┌───────────────────────────┴───────────────────────────────┐
        ▼                                                           ▼
 llama.cpp BGE-M3  :8081 (--embedding)                llama.cpp Qwen3-8B :8082
        MODEL SYSTEM (192.168.69.20 — same LAN)
```

| Service | Runs | Host port | Notes |
|---|---|---|---|
| `frontend` | nginx + built React SPA | **`0.0.0.0:8090`** | proxies `/api/*` → `backend:8000` |
| `backend` | FastAPI + pipeline | — (internal) | volumes: `uploads`, `config` |
| `qdrant` | `qdrant/qdrant` | **`0.0.0.0:6333`** | volume: `qdrant_storage` (persists); built-in **dashboard + REST API** for inspecting the embedded chunks |

> **Qdrant dashboard** (project-internal tooling): `http://<host-ip>:6333/dashboard` shows the
> collection, points, payloads (chunk text, source, page, chunk_id) and vector search — the
> direct way to inspect what the pipeline stored. The **Qdrant status dot in the app's header
> opens it in a new tab**. This is a concept, not a production system: keep both ports on the
> project LAN only.

🔒 **Port policy (model system):** port **8080 is reserved** (a pre-existing non-RAG service)
and must **never** be used by the RAG system. RAG ports there: **8081** embedding (BGE-M3),
**8082** summary (Qwen3-8B), 8083 whisper (full pipeline), 8084 VLM (full pipeline).

## 2. Prerequisites

1. **Docker** + the Compose plugin on the app host.
2. **Model system** (LAN IP `192.168.69.20`) with the two v1 model servers up — see
   `model-servers/` (startup scripts `start-bge-m3.sh` on **8081**, `start-qwen3-8b.sh` on
   **8082**, both bound `0.0.0.0`). Quick check from the app host:
   ```bash
   curl http://192.168.69.20:8081/v1/models   # BGE-M3  → "bge-m3"
   curl http://192.168.69.20:8082/v1/models   # Qwen3-8B → "qwen3-8b"
   ```
   (or one click per model in the app's Settings tab → **Test verbinding**)
3. **PDFs with a text layer** (KicMPi documents from the website). A scanned PDF will —
   correctly — be rejected with a clear in-app message. Quick check:
   ```bash
   python3 -c "import fitz,sys; d=fitz.open(sys.argv[1]); print(sum(1 for p in d if p.get_text().strip()),'/',len(d),'pages with text')" <file.pdf>
   ```
4. Host firewall: allow **inbound TCP 8090** (app) and, if you want dashboard access from other
   machines, **TCP 6333**.

## 3. Start the app

```bash
cp .env.example .env        # only if you want to override defaults (IPs, ports, …)
docker compose up -d --build
```

- First build pulls/builds ~3 images (a few minutes); afterwards `docker compose up -d` is fast.
- Verify: `curl http://localhost:8090/api/health` → `{"ok":true,...}` and open
  `http://<this-machine's-LAN-IP>:8090` (0.0.0.0 binding) — and
  `http://<this-machine's-LAN-IP>:6333/dashboard` for the Qdrant dashboard.
- All data lives in Docker volumes: `uploads` (PDFs + extracted Markdown + manifest),
  `config` (settings.json), `qdrant_storage` (vectors). Restart-safe:
  `docker compose down && up -d` keeps everything (Qdrant persistence).

## 4. Configure the app

**Model endpoints** — defaults already point at `192.168.69.20:8081/8082`. If the IP/port ever
changes, do it **in the UI** (no file edits, no restart):

1. Open **Instellingen**.
2. Enter the model system's IP:port per model (embedding, summary; VLM/ASR fields are stored
   for the full pipeline but unused in v1).
3. Click **Test verbinding** per endpoint → green ✓ with latency.
4. Click **Bewaar instellingen** → header status dots update immediately. Values persist to the
   `config` volume and override the `.env` defaults.

**Qdrant dashboard URL** — same tab: leave empty to auto-derive
(`http://<app-host>:6333/dashboard`), or set an explicit URL if the port mapping differs.

**The header status dots (Embeddings · Samenvatting · Qdrant)** are your pre-flight checklist:
all green = the full pipeline is live. The **Qdrant dot is a link** to the dashboard.

## 5. Using the app

**Documenten** — drag & drop (or click) a PDF. The table shows live pipeline progress
*Lezen → Chunken → Embedden → Opgeslagen*, chunk count, and status. The **filename is
clickable** and opens the original uploaded PDF in a new tab. Delete removes the files and all
its vectors.

**Zoeken** — Dutch query + top-k (3/5/10) + optional document filter. The **AI-samenvatting
appears first** (grounded, with `[bestandsnaam, p. N]` citations), below it the retrieved
chunks — **collapsed by default** (rank · score · file · page); the round arrow expands a
chunk's content. Clicking a chunk's **source filename** opens the original PDF.

**Instellingen** — model endpoints (see §4), dashboard URL, and **Demo-modus** (mock
embeddings — an offline development fallback only, off by default; toggling requires
re-ingesting the documents).

## 6. Operating the app

| Task | Command |
|---|---|
| Start | `docker compose up -d --build` (first time) / `docker compose up -d` |
| Logs | `docker compose logs -f backend` (or `frontend` / `qdrant`) |
| Restart everything | `docker compose down && docker compose up -d` (data persists) |
| Backend only | `docker compose restart backend` |
| Check health | `curl http://localhost:8090/api/health` |
| **Reset the whole concept** (empty corpus) | `docker compose down -v && docker compose up -d --build` |

Useful API endpoints (behind the UI):

```bash
curl http://localhost:8090/api/documents          # list docs + pipeline state
curl http://localhost:8090/api/status             # qdrant + model endpoint probes
curl -X POST http://localhost:8090/api/search \
     -H 'Content-Type: application/json' \
     -d '{"query":"Hoe werkt het voorbeeldproject?","top_k":5}'
curl -F "file=@/path/to/document.pdf" http://localhost:8090/api/documents
curl -OJ http://localhost:8090/api/documents/<doc_id>/file   # original uploaded PDF
# Qdrant REST API (direct, same data the app stores):
curl http://localhost:6333/collections
```

## 7. Troubleshooting

| Symptom | Check |
|---|---|
| Red **Embeddings** dot | `curl http://<model-ip>:8081/v1/models`; correct IP in Settings tab; 🔒 never 8080 |
| Red **Samenvatting** dot (chunks still work!) | `curl http://<model-ip>:8082/v1/models`; first inference can be slow (model warm-up) — run one test search |
| Red **Qdrant** dot | `docker compose ps`; `docker compose logs qdrant` |
| Dashboard doesn't open | Is `http://<host-ip>:6333/dashboard` reachable? Firewall TCP 6333; check the URL in the Settings tab |
| Upload rejected "geen geldig PDF" | File is not a PDF (magic-byte check) |
| Upload rejected "te groot" | Default limit 25 MB (`UPLOAD_MAX_MB`) |
| Doc ends in **Fout** "geen laaibare tekstlaag" | Scanned PDF — v1 has no OCR; use a text-layer PDF |
| App not reachable from LAN | Firewall: allow TCP **8090** inbound; the port is explicitly bound to `0.0.0.0` in `docker-compose.yml` |
| Slow first search | Model warm-up — normal; pre-warm with a test query |
| Toggled **Demo-modus** and results look weird | Mock vectors are keyword-ish; delete + re-upload documents after switching back to the real model |

> **Changing `EMBED_DIMS`** (vector size) requires a full reset (`down -v`), because existing
> vectors would have a different dimensionality.

## 8. Pipeline & design decisions (short)

- **Markdown is the only format downstream.** Every source is converted to one canonical
  Markdown file (`## Page N` sections) before chunking; v1's PDF path does this with
  PyMuPDF text-layer extraction and stores the file at `uploads/{doc_id}.md` for
  inspection. Adding video/audio/web later = adding a converter at the front — zero
  downstream changes (full pipeline: whisper.cpp ASR + Qwen3-VL, per the tooling doc).
- **Chunking:** structure-aware (page/paragraph boundaries), 200–350 words (≈280–480 real
  tokens), ~15 % sentence overlap.
- **IDs:** `chunk_id = sha256(doc_id:chunk_index)` (deterministic, idempotent re-ingest); the
  Qdrant point id is its first 128 bits (UUID requirement), the full id stays in the payload.
- **Embedding:** BGE-M3 dense, 1024-dim, cosine. llama.cpp rejects single inputs longer than
  its physical batch with HTTP 500 — the backend degrades adaptively (per-text retry,
  recursive sentence-bounded split + L2-normalised segment averaging), and the startup script
  sets `--batch-size 8192` as the clean fix.
- **Summary:** grounded Dutch prompt (answer only from the chunks, cite `[bron, pagina]`,
  abstain if unknown); `temperature 0.2`, thinking disabled for speed. Summary failure never
  blocks chunk retrieval.
- **Settings:** env defaults + runtime overrides persisted to the `config` volume, effective
  immediately.
- **Originals kept:** the uploaded PDF stays at `uploads/{doc_id}.pdf`, served back
  (`Content-Disposition: inline`) so results always link to the source document.

## 9. Project layout

```
.
├── README.md                  ← this file (project docs + operation runbook)
├── PLAN_WEBAPP_V1.md          ← v1 specification, decisions & execution log
├── docker-compose.yml         ← frontend + backend + qdrant (0.0.0.0:8090, 0.0.0.0:6333)
├── .env.example               ← copy to .env to override defaults
├── docs/KICMPI_STYLE_GUIDE.md ← branding (colors, fonts, components)
├── model-servers/             ← copy to the MODEL system (scripts + MODELS.md)
├── frontend/                  ← React + Vite + Tailwind → nginx
│   ├── Dockerfile · nginx.conf · package.json · vite.config.js · tailwind.config.js
│   ├── public/kicmpi-logo.svg
│   └── src/                   ← App, api client, Header/Hero, Documenten/Zoeken/Instellingen views
└── backend/                   ← FastAPI + ingestion pipeline
    ├── Dockerfile · requirements.txt
    └── app/
        ├── main.py · config.py (env + Settings-tab overrides) · schemas.py
        ├── store.py (Qdrant) · state.py (docs.json manifest)
        ├── pipeline/  pdf.py · chunking.py · embedding.py (real + mock) · summary.py
        └── routers/   documents.py · search.py · status.py (+ /probe) · settings.py
```

## 10. Roadmap (next iterations)

- **Full pipeline:** video/audio ingestion (whisper-large-v3 ASR + Qwen3-VL image-to-text) —
  converters plug in at the front, Markdown stays canonical.
- **Evaluation & tuning** (the core data-science work): evaluation set + metrics, retrieval
  quality experiments (chunk size/overlap, embedding model, top-k, hybrid/sparse retrieval),
  logged per CRISP-DM iteration for the report.
- Web-content ingestion, metadata labelling, reranking, auth/access levels — as scope allows.
