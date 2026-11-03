# Approach Plan — KicMPi RAG Web App, Concept v1 (client demo)

> **Status:** v1.1 — ready to execute in a dedicated session. *(v1.1, 2026-11-02: Markdown-canonical principle made explicit; **Settings tab added to scope** so the model system's IP:port can be entered in the UI; web app explicitly bound to **0.0.0.0** for LAN access; new §9 model-server prep with llama.cpp/whisper.cpp startup scripts in `model-servers/`; §11 records the resolved decisions from Tom.)*
> **Goal:** by **tomorrow morning** (client meeting with KicMPi) we have a **simple but complete concept web app** in which we can **demonstrate the entire RAG system process**: upload a PDF → watch it get parsed/chunked/embedded/stored → ask a search query → retrieve chunks (with scores + source/page) — with the **summary step present** (wired, visible) but not yet required to work fully.
> **Build location:** this directory (`github-repo/`). Everything software-related lives here; it will later be connected to the team's GitHub repo (Tom's task).
> **Companion docs:**
> - [`docs/KICMPI_STYLE_GUIDE.md`](docs/KICMPI_STYLE_GUIDE.md) — the KicMPi website style investigation (colors, fonts, components) that the app must follow.
> - Project root: `TOOLING_SELECTION_AND_PIPELINE.md` (locked stack + pipeline design), `SPRINT_PLAN.md` (sprint context), `sources/PROJECT_CONTEXT.md` (client & assignment context).

---

## 1. What "done" means (the demo promise)

> **Meeting format:** online — Tom shares his screen from the system where the app runs (this session's system). The app is reached at `http://<that-systems-LAN-or-public-IP>:8090` (bound to 0.0.0.0, see §4). The model system's address is entered **in the app's Settings tab** (or pre-set via `.env`), so it can change without any file edits.

The meeting demo must be able to show, **live, through the web UI only** (the client never touches files or the shell):

1. The app is up in Docker and looks like KicMPi (branding, colors, Dutch).
2. **Ingest:** we upload a KicMPi PDF through the UI and watch the pipeline run: *Lezen → Chunken → Embedden → Opgeslagen*, with live progress and chunk counts.
3. **Retrieve:** we type a Dutch query and relevant chunks come back from Qdrant with relevance scores, source filename and page.
4. **Summary (present):** the "AI-samenvatting" panel is always visible; it either shows a grounded summary with citations (if the summary model is connected) or a clean "nog in ontwikkeling / model niet verbonden" state. It must not break or hide the chunk results.
5. **Architecture story (30 s):** everything runs in Docker; the models (BGE-M3, Qwen3-8B) run **outside** the app on the model system, reached via IP:port (llama.cpp OpenAI-compatible endpoints); data never leaves our own infrastructure (AVG angle — important to KicMPi).
6. **Settings:** the model system's IP is entered once in the app's **Settings tab** (per model), a "Test verbinding" click turns the connection indicators green — no file editing, no terminal.

## 2. Fixed constraints (from the client-team requirement)

| # | Constraint | Consequence |
|---|---|---|
| C1 | **Whole web app runs in Docker containers only**, isolated from the host system | `docker compose` project; only the frontend port is published on the host; backend & Qdrant live on an internal Docker network; all data (uploads, vectors) in Docker volumes |
| C2 | **Clear frontend / backend distinction** | Separate containers: React+Vite+Tailwind frontend (served by nginx) vs. Python FastAPI backend vs. Qdrant container. No shared code, REST API between FE↔BE |
| C3 | **Models run OUTSIDE the app** (llama.cpp servers on the model system, same LAN) | The app only *calls* OpenAI-compatible endpoints via `EMBEDDING_BASE_URL` / `SUMMARY_BASE_URL` (IP:port) — defaults from env vars, **overridable at runtime in the app's Settings tab**. No model weights in the app, no GPU needed in the app |
| C4 | **Web-app-first UX** | Everything (upload, ingest status, search, summary, delete) is doable from the browser. No file-system or CLI dependency at demo time |
| C5 | **Simple — this is concept v1** | PDF-only ingestion (text layer), no video/audio/VLM converters, no auth, no multi-user, no production hardening. Scope is cut at §3.2 |

## 3. Scope

### 3.1 In scope (v1)

- Docker Compose project: `frontend` (nginx + React build), `backend` (FastAPI), `qdrant` (official image, persistent volume).
- Backend REST API: upload PDF, list/get/delete documents, live ingest status, search (top-k + optional doc filter), app/model status.
- Ingestion pipeline (v1, text-first): PDF → **text-layer extraction (PyMuPDF)** → canonical Markdown (same `## Page N` contract as `TOOLING_SELECTION_AND_PIPELINE.md` §3.4, so later vision/ASR converters plug in unchanged) → the Markdown file is **stored** (`uploads/{doc_id}.md`) for inspection/validation → **structure-aware chunking** (page/paragraph boundaries, ~256–512 token target, ~15 % overlap) → **BGE-M3 embedding** via `EMBEDDING_BASE_URL` (dense, 1024-dim) → **Qdrant** (cosine, indexed payload).
- **Settings (model endpoints in the UI):** Settings tab + `GET/PUT /api/settings` — enter the model system's IP:port per model (embedding, summary; fields for VLM + ASR reserved for the full pipeline), persisted to a config file on a Docker volume, effective immediately; env vars remain the defaults; "Test verbinding" per endpoint (green/red feedback).
- Search: query embedding → Qdrant top-k → chunks with score + payload metadata.
- Summary step: **wired and present** — calls `SUMMARY_BASE_URL` (Qwen3-8B via llama-server) with the grounded Dutch prompt from the tooling doc §3.7 (answer only from chunks, cite `[source, page]`, abstain if unknown); graceful degradation when unconfigured/unreachable (chunks are never blocked on it).
- Status endpoint + UI badges for Qdrant / embedding model / summary model connectivity (demo safety: we verify models before the client walks in).
- Frontend: KicMPi-branded React SPA, **Dutch UI**, 3 views (Documenten, Zoeken, Instellingen) + header/hero/status strip (see §6).
- Styling per `docs/KICMPI_STYLE_GUIDE.md` (blue `#1668B1`, magenta `#E5027E`, pill buttons, striped sections, Figtree font, real KicMPi logo — already in `frontend/public/kicmpi-logo.svg`).
- README: how to start models, start the app, and run the demo script; `.env.example`.
- Optional rehearsal safety net **only** (not a product feature, **off by default**): `EMBED_MOCK=1` → deterministic mock embedder (1024-dim) so the *whole flow* can be dry-run even if no model server is reachable (clearly labelled "demo-modus" in the status panel). The real system (real BGE-M3 + Qwen3-8B) is the deliverable — we do not rely on mock mode (resolved with Tom, see §11).

### 3.2 Out of scope (explicitly — next sprints)

- Video/audio ingestion, whisper.cpp, Qwen3-VL vision path (the full pipeline from the tooling doc stays the *target architecture*; v1 only replaces the PDF converter with a text-layer version for simplicity and to avoid depending on the heavy VLM during the demo).
- Web-content crawling/copy-paste ingestion, metadata labelling beyond `{source, page, type, title, doc_id}`, reranking, hybrid (sparse) retrieval, auth/access levels, i18n, logging/monitoring, load testing, deployment to a server (local Docker only).
- Any work in the report or on the data-collection track.

## 4. Architecture

### 4.1 Design principle: Markdown is the only format downstream

Per `TOOLING_SELECTION_AND_PIPELINE.md` §3.1 (core design decision), the full system **accepts** PDF, video, and audio — but **every source is converted into one canonical Markdown file before chunking**; from chunking onward (embedding → Qdrant → retrieval → summary) the system deals with **Markdown only**. **This plan is built on that principle:**

- The v1 PDF path produces exactly the canonical Markdown contract (tooling doc §3.4: `source:`/`type:`/… header block + `## Page N` sections) and stores it on the volume.
- Chunking, embedding, storage, retrieval and summary contain **no source-format knowledge** — they only ever see Markdown chunks + payload.
- Adding MP4 / MP3 / web content in later sprints = adding a converter at the front (FFmpeg → whisper.cpp → SRT→MD; frames → Qwen3-VL → MD; manual copy-paste is already MD) + accepting the file type in the upload UI. **Zero downstream changes.** The models for those converters (Qwen3-VL-8B, whisper-large-v3) run on the model system and are reached over IP:port like the others (§9).

### 4.2 Container topology

```
                        HOST (demo machine)
┌────────────────────────────────────────────────────────────────────────┐
│  Browser ── http://localhost:8090 ──────────────┐                      │
│                                                 │ (only published port)│
│  ┌─────────────── DOCKER COMPOSE (internal net: kicmpi) ───────────┐  │
│  │ ┌────────────┐   /api proxy   ┌─────────────────┐      ┌───────┐ │  │
│  │ │ FRONTEND   │ ─────────────► │ BACKEND         │ ───► │ QDRANT│ │  │
│  │ │ nginx:alpine│  (same net)   │ python:3.12     │      │ :6333 │ │  │
│  │ │ :80 (React  │                │ FastAPI :8000   │      │ vol:  │ │  │
│  │ │  build)     │                │ + pipeline      │      │ qdrant│ │  │
│  │ └────────────┘                │ vol: uploads/   │      └───────┘ │  │
│  │                               └───────┬─────────┘                │  │
│  └───────────────────────────────────────┼──────────────────────────┘  │
│                                          │ OpenAI-compatible HTTP       │
│            (IP:port — via .env defaults or the app's Settings tab)    │
│        ┌─────────────────────────────────┼────────────────────────┐   │
│        ▼                                 ▼                        │   │
│  llama.cpp server (BGE-M3, --embedding)  llama.cpp server (Qwen3-8B) │  │
│  http://<model-ip>:8081                  http://<model-ip>:8082      │  │
└────────────────────────────────────────────────────────────────────────┘
```

**Containers**

| Service | Image / build | Port (host) | Notes |
|---|---|---|---|
| `frontend` | build `frontend/Dockerfile` (multi-stage: `node:22-alpine` Vite build → `nginx:alpine`) | **`0.0.0.0:8090` → 80** | Serves the SPA; nginx proxies `/api/*` → `backend:8000` (no CORS issues, clean single URL) |
| `backend` | build `backend/Dockerfile` (`python:3.12-slim`, FastAPI + uvicorn) | — (internal only) | Depends on `qdrant`; volumes `uploads` + `config` |
| `qdrant` | `qdrant/qdrant` (current stable) | — (internal only) | Volume `qdrant_storage`; healthcheck `/healthz` |

> **LAN reachability (fixed constraint from Tom):** the compose file publishes the frontend port **explicitly bound to all interfaces** — `"0.0.0.0:8090:80"` — so any device on the same LAN (or the host itself) can open the app at `http://<server-IP>:8090`. The host firewall must allow port 8090 inbound. Backend and Qdrant stay on the internal Docker network only (never published) — that keeps the isolation intact while the web UI is the single entry point.

**Configuration (`.env` at repo root, copied from `.env.example`)**

| Variable | Default | Meaning |
|---|---|---|
| `APP_PORT` | `8090` | Published frontend port on the host |
| `QDRANT_URL` | `http://qdrant:6333` | Internal (compose) |
| `QDRANT_COLLECTION` | `kicmpi_documents` | Collection name |
| `EMBEDDING_BASE_URL` | `http://192.168.69.20:8081` ← *model system (Tom's, LAN)* | BGE-M3 llama.cpp server |
| `EMBEDDING_MODEL` | `bge-m3` | Model name passed in the request |
| `EMBED_DIMS` | `1024` | Vector size (BGE-M3 dense) |
| `SUMMARY_BASE_URL` | `http://192.168.69.20:8082` | Qwen3-8B llama-server (8082 — **8080 is reserved on the model system, never use it**) |
| `SUMMARY_MODEL` | `qwen3-8b` | Model name |
| `VLM_BASE_URL` | `http://192.168.69.20:8084` | Qwen3-VL-8B (reserved — full pipeline, unused in v1) |
| `ASR_BASE_URL` | `http://192.168.69.20:8083` | whisper wrapper (reserved — full pipeline, unused in v1) |
| `EMBED_MOCK` | `0` | `1` = deterministic mock embedder (demo safety net, see §3.1) |
| `UPLOAD_MAX_MB` | `25` | Upload limit (PDFs) |

> **IP note:** the model system's IP is **`192.168.69.20`** (Tom's machine on the team LAN; verified reachable from the demo server on 2026-11-02). It can be set here *or* in the app's Settings tab (which overrides these defaults at runtime and persists to a volume — that's the recommended way at the meeting). Compose also maps `host.docker.internal` → host-gateway on the backend, so `http://host.docker.internal:8081` works too if the models ever run on the *same* machine as the app.
>
> 🔒 **Port policy (Tom, 2026-11-02): port `8080` on the model system is RESERVED** (the agent's llama.cpp server). The RAG system — web app, scripts, defaults, future work — must **never** use port 8080 on that system. RAG ports there: 8081 (embedding), 8082 (summary), 8083 (whisper, later), 8084 (VLM, later).

**File tree to create**

```
github-repo/
├── README.md                        # setup + model commands + demo script
├── docker-compose.yml
├── .env.example
├── .gitignore
├── PLAN_WEBAPP_V1.md                # this file
├── docs/
│   ├── KICMPI_STYLE_GUIDE.md
│   └── assets/kicmpi-home-{top,full}.jpg
├── model-servers/                   # ← copy this folder to the MODEL system (not part of the Docker app)
│   ├── MODELS.md                    # which models, HF sources, quants, ports, VRAM budget, health checks
│   ├── start-bge-m3.sh              # llama.cpp --embedding (port 8081)
│   ├── start-qwen3-8b.sh            # llama-server (port 8080)
│   ├── start-qwen3-vl.sh            # llama-server + mmproj (port 8082)
│   ├── whisper_server.py            # minimal HTTP wrapper around whisper.cpp (port 8083)
│   └── start-whisper.sh             # runner for the wrapper (same restart-loop style)
├── frontend/
│   ├── Dockerfile                   # multi-stage build → nginx
│   ├── nginx.conf                   # SPA fallback + /api proxy → backend:8000
│   ├── package.json                 # react, react-dom, vite, tailwindcss
│   ├── vite.config.js               # dev proxy /api → localhost:8000 (dev only)
│   ├── tailwind.config.js           # KicMPi tokens (style guide §8)
│   ├── index.html
│   ├── public/kicmpi-logo.svg       # (already present)
│   └── src/
│       ├── main.jsx · App.jsx       # tabs: Documenten / Zoeken
│       ├── index.css                # tailwind + .bg-kicmpi-stripes
│       ├── api/client.js            # fetch wrapper for /api/*
│       └── components/
│           ├── Header.jsx           # logo, tabs (active=magenta), status dots
│           ├── Hero.jsx             # navy band: app name + "Concept — RAG" + model badges
│           ├── DocumentsView.jsx    # dropzone + doc table
│           ├── IngestProgress.jsx   # 4-step live progress (Lezen→Chunken→Embedden→Opgeslagen)
│           ├── SearchView.jsx       # query bar, top-k, doc filter, results
│           ├── ChunkCard.jsx        # score bar, page chip, source, chunk text
│           └── SummaryPanel.jsx     # always-present summary (ok / loading / unavailable)
└── backend/
    ├── Dockerfile
    ├── requirements.txt             # fastapi, uvicorn, httpx, qdrant-client, PyMuPDF, python-multipart
    └── app/
        ├── main.py                  # FastAPI app, CORS, include routers, /health
        ├── config.py                # env settings (pydantic-settings)
        ├── schemas.py               # Pydantic request/response models
        ├── store.py                 # Qdrant: ensure collection (cosine, 1024), upsert, scroll, delete-by-doc
        ├── state.py                 # docs.json manifest on the uploads volume (stages, counts, errors)
        ├── pipeline/
        │   ├── pdf.py               # PyMuPDF → canonical markdown (## Page N sections)
        │   ├── chunking.py          # structure-aware: page/paragraph boundaries, 256–512 token target, ~15 % overlap
        │   ├── embedding.py         # httpx → {EMBEDDING_BASE_URL}/v1/embeddings (batched); mock fallback
        │   └── summary.py           # httpx → {SUMMARY_BASE_URL}/v1/chat/completions (grounded NL prompt, citations, abstention)
        └── routers/
            ├── documents.py         # POST/GET/DELETE documents, ingest status, background ingestion task
            ├── search.py            # POST /search
            └── status.py            # GET /status (qdrant + both model endpoints + mock flag)
```

## 5. Backend specification

### 5.1 API (all under `/api`)

| Method & path | Body / params | Returns |
|---|---|---|
| `POST /documents` | multipart file (`application/pdf` only) | `{doc_id, filename, status: "uploaded"}` — ingestion starts as a background task |
| `GET /documents` | — | list: `{doc_id, filename, uploaded_at, status, stage, progress, chunks, error?}` |
| `GET /documents/{id}` | — | same as one list item (poll target for live progress) |
| `DELETE /documents/{id}` | — | removes file, manifest entry and its vectors (payload filter `doc_id`) |
| `POST /search` | `{query, top_k=5, doc_id?}` | see 5.2 |
| `GET /status` | — | see 5.3 |
| `GET /settings` | — | current effective settings (model endpoints + models, mock flag) |
| `PUT /settings` | `{embedding_url?, embedding_model?, summary_url?, summary_model?, vlm_url?, vlm_model?, asr_url?, asr_model?, embed_mock?}` | updated settings — persisted to a config file on the `config` volume, effective immediately (overrides env defaults; VLM/ASR are stored for the full pipeline but unused in v1) |

### 5.2 Search response

```json
{
  "query": "Hoe start je de cluster in het voorbeeldproject?",
  "chunks": [
    {"chunk_id": "…", "doc_id": "…", "source": "presentatie-2025-04.pdf",
     "title": "…", "page": 12, "score": 0.81, "text": "## Page 12\n…markdown…"}
  ],
  "summary": {"status": "ok|unconfigured|error:<msg>", "model": "qwen3-8b",
              "text": "Korte samenvatting … [presentatie-2025-04.pdf, p.12]"},
  "took_ms": 142
}
```

- `summary.text` is `null` unless `status == "ok"`. **Chunk retrieval must succeed independently of the summary model** (summary failure → `status: "error: …"`, chunks still returned).
- `score` = Qdrant cosine similarity. Empty corpus / no matches → `chunks: []` + friendly UI message (Dutch).

### 5.3 Status response

```json
{"app": "ok", "mock_mode": false,
 "qdrant": {"ok": true},
 "embedding": {"ok": true, "url": "http://…:8081", "latency_ms": 14},
 "summary":   {"ok": false, "reason": "connection refused"}}
```

Probes `GET {base}/v1/models` with a short timeout (1.5 s). The frontend header shows 3 green/red dots (Embeddings · Samenvatting · Qdrant); `mock_mode: true` renders an amber "demo-modus" badge.

### 5.4 Ingestion pipeline (per upload)

1. **Validate** (PDF magic bytes, size ≤ `UPLOAD_MAX_MB`) → save to volume `uploads/{doc_id}.pdf`; manifest entry `status: uploaded`.
2. **Parsing** (`stage: parsing`): PyMuPDF, per-page text → canonical Markdown `## Page N` sections (tooling doc §3.4 contract). *If a page yields no text* → collect; if **zero** pages have text (scanned PDF) → `status: error`, message "Dit PDF heeft geen laaibare tekstlaag (scan?). Deze conceptversie ondersteunt nog geen OCR." (the full pipeline's vision path is the documented upgrade).
3. **Chunking** (`stage: chunking`): split on page boundaries + blank-line/paragraph splits; merge small sections up to ~256–512 token target (token ≈ whitespace-split words, deterministic); ~15 % overlap by carrying trailing sentences across boundaries. Each chunk payload: `{chunk_id, doc_id, source, title (doc filename stem), type: "pdf", page, chunk_index, language: "nl", chunk_markdown}`.
4. **Embedding** (`stage: embedding`): batch 16 chunks/request → `{EMBEDDING_BASE_URL}/v1/embeddings`; progress = embedded/total. Mock mode: deterministic 1024-dim vector (hashed bag-of-words, L2-normalised) — retrieval then degrades to keyword-ish matching, which is fine for a labelled demo fallback.
5. **Storing** (`stage: stored`): Qdrant upsert (collection created on first use: cosine, `EMBED_DIMS`, payload indexes on `doc_id`, `type`, `page`); `chunk_id = sha256(doc_id:chunk_index)` (idempotent re-ingest). Manifest `status: stored`, `chunks: N`.

Ingestion runs in a background thread (single-worker app); stage/progress/error are written to the manifest after each step so the UI can poll at 1–2 s.

### 5.5 Summary call (present, best-effort)

System prompt (Dutch, per tooling doc §3.7): *"Beantwoord de vraag uitsluitend op basis van de meegegeven chunks. Wees beknopt. Vermeld bij elke bewering de bron als [bron, pagina]. Als de chunks het antwoord niet bevatten, zeg dan expliciet dat er in het corpus geen antwoord gevonden is."* User message: the query + numbered chunks. `temperature 0.2`, `max_tokens ≈ 400`. Timeout 60 s → on failure: `status: "error: …"`.

## 6. Frontend specification (React + Vite + Tailwind, Dutch UI)

**Design system:** exactly per `docs/KICMPI_STYLE_GUIDE.md` §8 (Tailwind tokens), plus:
- `Header`: white sticky, `kicmpi-logo.svg` left (h-12), tabs right: **Documenten · Zoeken · Instellingen** — active tab **magenta** (like the site's nav), 3 status dots (green/red/amber) far right with tooltip (Embeddings / Samenvatting / Qdrant); dots refresh after every settings save and on view switch.
- `Hero`: compact navy (`#0B3356`) band: "KicMPi Kennisassistent" (white, bold) + "Concept — RAG prototype" magenta label + one-line Dutch subtitle. (No industrial photo needed; navy gradient is the approved stand-in.)
- Buttons: pill, blue → navy hover; white variant with magenta text; `more-link` style "»".
- Alternating white / `.bg-kicmpi-stripes` sections; blue bold section titles; magenta for dates/labels/highlights; cards ≤ 8 px radius; circular status icons where an icon suits.

**View 1 — Documenten**
- Upload zone (drag & drop + click, PDF only) → `POST /api/documents` → row appears in the table with **live progress**: 4 steps *Lezen → Chunken → Embedden → Opgeslagen* (check icons + % bar; polling 1.5 s). Error state shows the backend message in a red-ish banner (keep palette: use magenta only for accents, errors use `#A51B00`-style red already present in Drupal's palette).
- Table: bestandsnaam · geüpload (dd-mm-yyyy) · chunks · status pill (Bewerkt = blue, Werkt = amber, Fout = red) · delete (trash icon, confirm).
- Empty state: friendly Dutch hint ("Sleep een PDF hierheen om de RAG-pijplijn te zien draaien").

**View 2 — Zoeken**
- Big pill search input + "Zoeken" button; options row: top-k select (3/5/10) + document filter select (Alles + each doc).
- Results: `ChunkCard` list — score bar (0–1, blue), page chip ("p. 12"), source filename (magenta), chunk text in a pre-wrap card. Count line: "8 chunks gevonden in 142 ms".
- `SummaryPanel` — **always rendered** under the results: title "AI-samenvatting" (blue). States: *loading* (spinner "Samenvatting genereren…"), *ok* (text + inline citations), *unconfigured/unavailable* (neutral gray box: "De samenvatting-functie is in deze conceptversie nog niet volledig beschikbaar — de opgehaalde chunks hierboven zijn de bron." + a small "model niet verbonden" hint if status says so), *error* (same box + reason).
- Empty results: "Geen relevante chunks gevonden. Probeer een andere vraag of een bredere top-k."

**View 3 — Instellingen**
- **Model endpoints:** four endpoint groups — *Embedding model* (URL + model name), *Samenvatting model* (URL + model name), *Visie-model (PDF/video → tekst)* and *Audio-model (video/audio → tekst)* — the last two stored now, greyed hint "wordt in de volgende sprint gebruikt" (reserved for the full pipeline, so the UI doesn't need rework later).
- Per endpoint: **"Test verbinding"** button → calls the status probe, inline green ✓ / red ✗ feedback with latency.
- **"Bewaar instellingen"** (blue pill) → `PUT /api/settings` → header status dots update; success message "Instellingen opgeslagen".
- **Demo-modus** toggle (mock embeddings) with an explicit amber note: "Alleen voor proefdraaien — de echte modellen staan uit."
- All labels in Dutch; no terminal/file knowledge needed to operate the app (constraint C4).

**Behavioural rules:** all fetches through `api/client.js`; every async state has loading/empty/error variants; no console errors on normal flows; app usable end-to-end even with zero documents (empty states) and with models offline (red dots + graceful messages).

## 7. Demo plan for the client meeting (tomorrow morning)

**Prerequisites (rehearse today + re-verify ~1 h before the meeting):**
1. On the **model system**: BGE-M3 + Qwen3-8B servers up (scripts `model-servers/start-bge-m3.sh` + `start-qwen3-8b.sh`, ports **8081** + **8082**, both bound `0.0.0.0`). ✅ *Already done on 2026-11-02 — re-verify only.*
2. On the **demo server** (this session's system): `docker compose up -d --build`; verify from *another* device on the LAN that `http://<demo-server-ip>:8090` opens (0.0.0.0 binding works, firewall open).
3. In the app's **Settings tab**: enter the model system's IP once, "Test verbinding" → all green. (Or pre-set `.env` — same effect.)
4. All 3 header dots green (or amber demo-modus only if `EMBED_MOCK=1` — not the plan).
5. 2–3 KicMPi **text-layer** PDFs (Tom downloads them from the website) ready in a folder next to the screen; one pre-ingested so the document list isn't empty.

**Demo script (~8–10 min, live):**
1. Open app → 15 s: "Dit is de concept-kennisassistent; alles draait lokaal in Docker, de modellen draaien buiten op het model-systeem — geen data verlaat het gebouw (AVG)."
2. **Ingest:** upload a KicMPi PDF → point at the 4 pipeline steps running live ("lezen → chunken → embedden → opgeslagen in Qdrant") until "Opgeslagen · N chunks".
3. **Retrieve:** type a Dutch question about the document → chunks appear with scores + "p. X" + source name ("dit is de vectorzoeking met BGE-M3").
4. **Summary:** show the panel (grounded summary with `[bron, p.]` citations if the model is up; otherwise the honest "nog in ontwikkeling" state — both are pre-agreed with the client as v1 scope).
5. Close: what's next (full pipeline with video/audio, evaluation, tuning) — one slide or 30 s of talk, no new scope promises.

**Fallbacks (in order):**
- Model server down at meeting time → status dots show it honestly; if `EMBED_MOCK=1` is enabled the flow still runs end-to-end (labelled demo-modus); summary panel in its "unavailable" state.
- Worst case (Docker dies or the network hiccups during the online meeting) → pre-recorded screen capture of the rehearsal run (record during the P5 rehearsal).
- Scanned/OCR-less PDF picked by mistake → clear in-app error; only bring verified text-layer PDFs.

## 8. Execution plan (for the implementation session)

Ordered phases; each has a **checkpoint** — if a checkpoint fails, fix before moving on. Time estimates assume one focused session; the cut line is marked.

| Phase | Work | Est. | Checkpoint (Definition of Done) |
|---|---|---|---|
| **P0 — Scaffold** | repo files: `docker-compose.yml`, `.env.example`, both `Dockerfile`s, `nginx.conf`, minimal FastAPI (`/health`), minimal React app with KicMPi header + hero + tokens | ~45 min | `docker compose up --build` → `http://localhost:8090` shows the branded shell; `/api/health` ok through nginx |
| **P1 — Ingestion backend** | `pdf.py`, `chunking.py`, `store.py`, `state.py`, documents router + background ingestion; Qdrant upserts | ~1.5 h | `curl` upload of a sample PDF → `GET /documents/{id}` walks `parsing→chunking→embedding→stored` (embedding: mock or real) with correct chunk count; Qdrant scroll shows payloads |
| **P2 — Search + summary + settings wiring** | `embedding.py` (real + mock), `summary.py`, search router, status router, **settings store + router** (config file on `config` volume, overrides env, effective immediately) | ~1.5 h | `POST /search` returns scored chunks with page/source (real model if up, else mock); summary returns `ok` when the model is up, `unconfigured/error` otherwise — chunks always returned; `PUT /settings` changes the embedding endpoint and the next request uses it |
| **P3 — Frontend** | api client; Header/Hero/status dots; DocumentsView (+upload, live progress, list, delete); SearchView (+results, filters, SummaryPanel); **SettingsView** (endpoint fields for all 4 models, per-endpoint "Test verbinding", save, demo-modus toggle); empty/loading/error states | ~3 h | Full flow in the browser: upload → watch progress → search → chunks + summary panel; **Settings tab: enter the model system's IP → test turns green → search works**; models-off state renders gracefully (red dots, no crashes) |
| **P4 — Integration & runbook** | `.env` polish, README (model commands, compose commands, demo script), edge cases (no-text-layer PDF, empty corpus, 25 MB+ upload rejected, duplicate re-ingest), final `docker compose down && up` restart test (Qdrant persistence), **LAN test from a second device**: open `http://<demo-server-ip>:8090` in another machine's browser and run one search | ~1 h | README works copy-paste on a clean machine; demo script executed once fully; app demonstrably reachable over the LAN, not just localhost |
| **P5 — Rehearsal** | dress rehearsal of §7 script with a real KicMPi PDF; fix wobbles; **record screen capture** as the worst-case fallback | ~30 min | 10-min demo runs without any manual intervention; recording saved |

**Cut line (if time runs out):** P3 minimal = upload + doc list + search + chunk cards + summary panel placeholder (no delete, no doc filter, no top-k select). P4/P5 are non-negotiable (runbook + rehearsal) — they are what make the demo safe.

## 9. Model servers — what must run on the model system (prep for Tom)

All models come from **Hugging Face in GGUF format** and run on Tom's model system (same LAN as the demo server). The web app reaches them **only via IP:port** (entered in the app's Settings tab or pre-set in `.env`). Ready-to-use startup scripts (same restart-loop style as the team's existing llama.cpp script) are in [`model-servers/`](model-servers/) — copy that folder to the model system and adjust the model paths.

| # | Model | Role in the RAG system | Runtime | Hugging Face source (GGUF) | Quant (recommended) | ≈ Size | Port |
|---|---|---|---|---|---|---|---|
| 1 | **BGE-M3** | Embedding — turns Markdown chunks + user queries into dense 1024-dim vectors | llama.cpp `llama-server --embedding` | [`lm-kit/bge-m3-gguf`](https://huggingface.co/lm-kit/bge-m3-gguf) | **f16** (q8_0 fallback) | ≈1.1 GB | **8081** |
| 2 | **Qwen3-8B** | Summary — grounded NL answer from retrieved chunks | llama.cpp `llama-server` | [`Qwen/Qwen3-8B-GGUF`](https://huggingface.co/Qwen/Qwen3-8B-GGUF) | **Q4_K_M** | ≈5–6 GB | **8082** ⚑ |
| 3 | **Qwen3-VL-8B-Instruct** | Image-to-text — PDF pages + video frames → Markdown (full pipeline, later sprint) | llama.cpp `llama-server --mmproj` | [`Qwen/Qwen3-VL-8B-Instruct-GGUF`](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct-GGUF) (+ its mmproj file) | **Q4_K_M** + mmproj **Q8_0** (f16 fallback) | ≈6–8 GB incl. mmproj | **8084** |
| 4 | **whisper-large-v3** | Audio-to-text — video audio + MP3 → timestamped SRT (full pipeline, later sprint) | **whisper.cpp** — *sister project of llama.cpp, same GGUF format, but a different binary with no HTTP server of its own* → minimal wrapper provided | [`ggerganov/whisper.cpp` models](https://huggingface.co/ggerganov/whisper.cpp/tree/main/models) (`ggml-large-v3`) | **q8_0** (f16 for max accuracy) | ≈1.6 GB (runs fine on CPU) | **8083** |

**What v1 (tomorrow) needs: #1 + #2 only** (≈7 GB VRAM). #3 + #4 belong to the full pipeline (later sprints) — prepare them now if the hardware allows, but they are **not** demo blockers.

> ⚑ **Port note (2026-11-02, real layout on the model system `192.168.69.20`):** **port 8080 is RESERVED there** (existing agent llama.cpp server) and must never be used by the RAG system. So **Qwen3-8B (summary) runs on 8082** and BGE-M3 (embedding) on 8081; the VLM (later sprint) is assigned **8084** (whisper keeps 8083). Both servers are **up and verified reachable** from the demo server on 2026-11-02. The web app picks all of this up from its Settings tab, so any future port change is a UI-only matter.

**VRAM budget (all four at once, one GPU):** ≈13–16 GB → comfortable on a 24 GB card; workable on 16 GB if whisper runs on CPU (it's fine there) and the VLM is only needed at ingestion time — per tooling doc §3.9 the VLM (ingestion) and summary LLM (query time) rarely overlap.

**Health checks** (from the demo server or any LAN machine — the Settings tab's "Test verbinding" does exactly this):

```bash
curl http://<model-ip>:8081/v1/models    # BGE-M3    (embedding)
curl http://<model-ip>:8082/v1/models    # Qwen3-8B  (summary)
curl http://<model-ip>:8084/v1/models    # Qwen3-VL  (image-to-text, later sprint)
curl http://<model-ip>:8083/v1/models    # whisper wrapper (audio-to-text, later sprint)
```

> Note (kept consistent with the tooling doc's decision log): whisper runs in **whisper.cpp, not llama.cpp** — the "GGUF everywhere" constraint holds at the format/ecosystem level (same ggml family), and both runtimes are named separately in all docs.

## 10. Risks & mitigations (demo-day)

| Risk | Likelihood | Mitigation |
|---|---|---|
| Model servers not reachable at meeting time (network/IP/`host.docker.internal` on Linux) | Medium | P2 checkpoint verifies reachability **today**; `.env` takes a plain IP too; `EMBED_MOCK` fallback; pre-recorded capture |
| Demo PDFs lack a text layer (scans) | Medium | Verify each candidate PDF with PyMuPDF today; bring 3+ candidates; in-app error message is a feature, not a bug |
| First `docker compose up` too slow at the venue | Low-Med | Containers pre-started before clients arrive (`up -d`); images pre-pulled today |
| Slow first inference (model warm-up) makes the demo feel broken | Low-Med | Pre-warm: run one test query before the meeting; show the search after ~2 s is normal |
| Scope creep in the meeting (client asks for X now) | High (known client risk) | v1 scope is fixed by §3.2; feedback is *recorded* for the next sprint, not implemented |
| Frontend polish eats the whole day | Medium | Cut line above; branding tokens are ready so styling is fast, not exploratory |

## 11. Decisions & answers (resolved with Tom, 2026-11-02)

- **Model servers:** they run on Tom's system (LAN IP **192.168.69.20**, same LAN as the demo server); the meeting is **online** (screen share). The model system's IP is entered via the app's **Settings tab** (or `.env`), so a changing IP is a non-event → Settings view added to scope (§3.1, §5.1, §6 View 3). **BGE-M3 (:8081) + Qwen3-8B (:8082) downloaded, running, and verified reachable from the demo server (2026-11-02).** 🔒 **Port 8080 on the model system is reserved (agent server) and must never be used by the RAG system.**
- **Demo PDFs:** Tom downloads a few KicMPi PDFs from the website for demo + development → runbook keeps the text-layer verification step for each file.
- **Where the app runs:** on this session's system (the demo server); it must be **system-independent** → Docker-only + explicit `0.0.0.0:8090` binding, reachable from the LAN (§4.2).
- **Mock fallback:** accepted as an optional, **off-by-default** rehearsal safety net only — the real system (BGE-M3 + Qwen3-8B) is the deliverable and must work on its own; we do not rely on mock mode.
- **Font:** decided — **Figtree** (free, closest available to the licensed Typekit font Prometo); one-line Tailwind swap later if the client ever provides a Prometo licence.

**Assumptions (flag if wrong):** UI language = Dutch; single demo user, no auth; demo PDFs are text-based (to be verified); the summary step being *present-but-limited* is acceptable to the client (agreed in the requirement).

---

## 12. Execution log (2026-11-03, implementation session)

**All phases P0–P5 executed; every checkpoint passed.** The app is running on the demo
server (Docker, `0.0.0.0:8090`, also reachable at `http://192.168.69.12:8090`) with two
KicMPi PDFs pre-ingested (14 chunks), all three status dots green, and the models
pre-warmed via a test search.

| Phase | Result |
|---|---|
| P0 scaffold | ✅ `docker compose up --build` → branded shell at :8090, `/api/health` ok through nginx, Qdrant healthy (bash `/dev/tcp` healthcheck — the qdrant image has no curl/wget) |
| P1 ingestion | ✅ real upload walks `parsing→chunking→embedding→stored`; canonical Markdown stored in `uploads/{doc_id}.md`; Qdrant payloads verified. **Fix:** Qdrant point ids are 128-bit UUIDs — the 256-bit sha256 `chunk_id` is encoded via its first 128 bits (full id kept in payload) |
| P2 search/summary/settings | ✅ scored chunks + page/source; grounded Dutch summaries with `[bestandsnaam, p. N]` citations (citation format made explicit in the system prompt after the model echoed the placeholder); `PUT /settings` effective immediately + persisted to `config` volume. **Fix:** API field names (`embedding_url`) now mapped to store keys (`embedding_base_url`) — overrides were silently dropped before |
| P3 frontend | ✅ all 3 views + header/hero/dots; drag-&-drop upload with live 4-step progress; search with top-k + doc filter; SummaryPanel always present; Settings tab with per-endpoint "Test verbinding" (✓ latency / ✗ reason) + demo-modus toggle. Zero console errors in rehearsal |
| P4 integration & runbook | ✅ README written; edge cases verified: scanned PDF → clear Dutch OCR error, 26 MB upload → 413, non-PDF → 415, empty corpus → friendly message, `down && up` restart → data persists, LAN binding verified via `http://192.168.69.12:8090` |
| P5 rehearsal | ✅ full demo flow run in the browser with the real KicMPi PDFs (screenshots taken); models warm. *Not done:* screen **recording** of the run (no capture tool in this session) — if Tom wants the worst-case fallback video, record one 10-min run before the meeting |

**⚠ Key finding (affects the model system):** the BGE-M3 llama.cpp server was started with
`--batch-size 512`; llama.cpp then rejects any single input > 512 **tokens** with
`HTTP 500 "input is too large to process"`. Dutch technical text tokenizes at up to ~2.3
tokens/word, so chunks of ~230+ words were rejected. Two-part fix:
1. `model-servers/start-bge-m3.sh` now sets `--batch-size 8192` — **Tom should restart the
   embedding server with the updated script** (one-liner; the web app works either way).
2. The backend now degrades adaptively: when the server says "too large", the batch is
   retried per-text and offending texts are recursively split at a sentence boundary with
   segment-vector averaging (L2-normalised) — robust for any server batch size.

Chunk targets were set to 200–350 words ≈ 280–480 real tokens (inside the plan's 256–512
token band and inside the current server limit, so most chunks embed natively).

**Demo state at handover:** stack running; corpus = `20251211_-_kennismaking_met_123atex.eu_-_waterstof.pdf`
(4 chunks) + `20251111_kic_mpi_-_gacs_presentatie_1.pdf` (10 chunks); settings point at
`192.168.69.20:8081/8082`; mock mode off. Morning checklist: README §9.

**v1.1 UX addendum (2026-11-03, requested by Tom before the 10.30 meeting) — done & verified:**
1. **Summary above chunks** in Zoeken: count line → *AI-samenvatting* panel → chunk list
   (the summary is based on the chunks listed below it).
2. **Chunks collapsed by default**: header row shows expand-arrow, rank, score bar, page chip
   and source file; the full chunk content is revealed per card via the round arrow
   (`ChunkCard` local state; new search results start collapsed again).
3. **Source file clickable** (in results *and* in the Documenten table): opens the original
   uploaded PDF in a new tab via `GET /api/documents/{doc_id}/file`
   (`Content-Disposition: inline`, browser PDF viewer). The original PDF is already kept on the
   uploads volume per document (`uploads/{doc_id}.pdf`) — no new storage needed.
All three verified in the browser (DOM order, collapsed state, expand click, new-tab PDF load);
zero console errors. Tom restarted the BGE-M3 server with `--batch-size 8192` on the model
system; corpus re-ingested fresh (14 points).
