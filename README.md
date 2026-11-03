# KicMPi Kennisassistent — concept (RAG web app, v1)

A simple but complete **concept web app** to demonstrate the entire RAG system process, built for
the KicMPi client meeting: upload a PDF → watch it get **parsed → chunked → embedded → stored**
in Qdrant → ask a Dutch query → retrieve chunks **with scores, source and page** → get a grounded
**AI summary** (wired and present; degrades gracefully when the summary model is not connected).

- **Language:** Dutch UI
- **Stack:** React + Vite + Tailwind (served by nginx) · Python FastAPI · Qdrant — all in Docker
- **Models run OUTSIDE the app** on the model system (same LAN): BGE-M3 (embeddings) and
  Qwen3-8B (summaries) behind llama.cpp OpenAI-compatible endpoints, reached **only via IP:port**
  — entered once in the app's **Settings tab**. No model weights in the app, no GPU needed here,
  **data never leaves our own infrastructure** (the AVG story for the meeting).

See `PLAN_WEBAPP_V1.md` for the full specification and `docs/KICMPI_STYLE_GUIDE.md` for the
branding. `model-servers/` holds the startup scripts for the model system (copy that folder there).

---

## 1. Architecture

```
                        DEMO SERVER (this machine)
┌────────────────────────────────────────────────────────────────────────┐
│  Browser (any LAN device) ── http://<server-ip>:8090 ─┐               │
│                                                       │ (only port)   │
│  ┌────────────── DOCKER COMPOSE (net: kicmpi-rag) ──────────────┐     │
│  │ ┌──────────────┐  /api proxy  ┌──────────────────┐  ┌───────┐│    │
│  │ │ FRONTEND     │ ───────────► │ BACKEND          │─►│QDRANT ││    │
│  │ │ nginx:alpine │              │ python:3.12      │  │ vol:  ││    │
│  │ │ + React SPA  │              │ FastAPI :8000    │  │qdrant ││    │
│  │ └──────────────┘              │ vol: uploads/    │  └───────┘│    │
│  │                               │ vol: config/     │           │    │
│  └───────────────────────────────┼──────────────────┘           │    │
│                                  │ OpenAI-compatible HTTP       │    │
│            (IP:port — .env defaults or the app's Settings tab)  │    │
└──────────────────────────────────┼───────────────────────────────┘
        ┌───────────────────────────┴──────────────────────────────┐
        ▼                                                          ▼
 llama.cpp BGE-M3  :8081 (--embedding)            llama.cpp Qwen3-8B :8082
        MODEL SYSTEM (192.168.69.20 — same LAN)
```

| Service | Runs | Host port | Notes |
|---|---|---|---|
| `frontend` | nginx + built React SPA | **`0.0.0.0:8090`** | proxies `/api/*` → `backend:8000` |
| `backend` | FastAPI + pipeline | — (internal) | volumes: `uploads`, `config` |
| `qdrant` | `qdrant/qdrant` | — (internal) | volume: `qdrant_storage` (persists) |

🔒 **Port policy (model system):** port **8080 is reserved** (the agent's llama.cpp server) and
must **never** be used by the RAG system. RAG ports there: **8081** embedding (BGE-M3), **8082**
summary (Qwen3-8B), 8083 whisper (later), 8084 VLM (later).

## 2. Prerequisites

1. **Docker** + the Compose plugin on the demo server (verified: Docker 29.x / Compose v5).
2. **Model system** (Tom's machine, LAN IP `192.168.69.20`) with the two v1 model servers up —
   see `model-servers/` (startup scripts `start-bge-m3.sh` on **8081**, `start-qwen3-8b.sh` on
   **8082**, both bound `0.0.0.0`). Quick check from the demo server:
   ```bash
   curl http://192.168.69.20:8081/v1/models   # BGE-M3  → "bge-m3"
   curl http://192.168.69.20:8082/v1/models   # Qwen3-8B → "qwen3-8b"
   ```
3. **2–3 KicMPi PDFs with a text layer** (Tom downloads them from the website). Verify each one
   before the meeting (a scanned PDF will — correctly — be rejected with a clear in-app message):
   ```bash
   python3 -c "import fitz,sys; d=fitz.open(sys.argv[1]); print(sum(1 for p in d if p.get_text().strip()),'/',len(d),'pages with text')" <file.pdf>
   ```
4. Host firewall: allow **inbound TCP 8090** so other LAN devices can open the app.

## 3. Start the app (demo server)

```bash
cd github-repo
cp .env.example .env        # only if you want to override defaults (IP, port, …)
docker compose up -d --build
```

- First build pulls/builds ~3 images (a few minutes); afterwards `docker compose up -d` is fast.
- **Start the stack before the clients arrive** — do not rely on a fresh build at meeting time.
- Verify: `curl http://localhost:8090/api/health` → `{"ok":true,...}` and open
  `http://<this-machine's-LAN-IP>:8090` **from another device on the LAN** (0.0.0.0 binding).
- All data lives in Docker volumes: `uploads` (PDFs + extracted Markdown + manifest),
  `config` (settings.json), `qdrant_storage` (vectors). Restart-safe: `docker compose down && up -d`
  keeps everything (Qdrant persistence).

## 4. Point the app at the model system

Defaults already point at `192.168.69.20:8081/8082`. If the IP ever changes, do it **in the UI**:

1. Open **Instellingen**.
2. Enter the model system's IP:port per model (embedding, summary; VLM/ASR are stored for the
   full pipeline but unused in v1).
3. Click **Test verbinding** per endpoint → green ✓ with latency.
4. Click **Bewaar instellingen** → header status dots update immediately; no restart, no files.

The three header dots (**Embeddings · Samenvatting · Qdrant**) are your pre-flight checklist:
all green ≈ 1 h before the meeting, then again right before the client joins.

## 5. Demo script (~8–10 min, live, screen share)

1. **Open the app** (15 s): “Dit is de concept-kennisassistent. Alles draait lokaal in Docker;
   de modellen draaien buiten, op het model-systeem — geen data verlaat het gebouw (AVG).”
2. **Ingest:** upload a KicMPi PDF → point at the four pipeline steps running live
   (*Lezen → Chunken → Embedden → Opgeslagen*) until “Opgeslagen · N chunks”.
3. **Retrieve:** type a Dutch question about the document → the **AI-samenvatting appears
   first** (grounded, with `[bestandsnaam, p. N]` citations), below it the retrieved chunks —
   **collapsed by default** (score · file · page). “Dit is vectorzoeken met BGE-M3.” Click the
   round arrow to reveal a chunk's content; click the **filename** to open the original PDF in
   a new tab.
4. **Summary:** show the *AI-samenvatting* panel — grounded Dutch summary with
   `[bron, p.]` citations when the model is up; otherwise the honest
   “nog niet volledig beschikbaar” state (pre-agreed v1 scope).
5. **Close:** what's next (full pipeline incl. video/audio, evaluation, tuning) — 30 s, no new
   scope promises. Record feedback for the next sprint, don't implement.

**Fallbacks (in order):**
- Model server down at meeting time → status dots show it honestly; the summary panel shows its
  “unavailable” state. If `EMBED_MOCK=1` is on, the flow still runs end-to-end (labelled
  *demo-modus*) — this is a rehearsal safety net only, **not** the deliverable.
- Worst case (Docker dies mid-meeting) → play the **pre-recorded screen capture** of the rehearsal.
- Scanned/OCR-less PDF picked by mistake → clear in-app error; only bring verified text-layer PDFs.

## 6. Operating the app

| Task | Command |
|---|---|
| Start | `docker compose up -d --build` (first time) / `docker compose up -d` |
| Logs | `docker compose logs -f backend` (or `frontend` / `qdrant`) |
| Restart everything | `docker compose down && docker compose up -d` (data persists) |
| Backend only | `docker compose restart backend` |
| Check health | `curl http://localhost:8090/api/health` |
| **Reset the whole concept** (empty corpus) | `docker compose down -v && docker compose up -d --build` |

Useful API endpoints (behind the UI, for rehearsals):

```bash
curl http://localhost:8090/api/documents          # list docs + pipeline state
curl http://localhost:8090/api/status             # qdrant + model endpoint probes
curl -X POST http://localhost:8090/api/search \
     -H 'Content-Type: application/json' \
     -d '{"query":"Hoe werkt het voorbeeldproject?","top_k":5}'
curl -F "file=@/path/to/document.pdf" http://localhost:8090/api/documents
curl -OJ http://localhost:8090/api/documents/<doc_id>/file   # original uploaded PDF
```

## 7. Troubleshooting

| Symptom | Check |
|---|---|
| Red **Embeddings** dot | `curl http://<model-ip>:8081/v1/models`; correct IP in Settings tab; 🔒 never 8080 |
| Red **Samenvatting** dot (chunks still work!) | `curl http://<model-ip>:8082/v1/models`; first inference can be slow (model warm-up) — run one test search before the meeting |
| Red **Qdrant** dot | `docker compose ps`; `docker compose logs qdrant` |
| Upload rejected “geen geldig PDF” | File is not a PDF (magic-byte check) |
| Upload rejected “te groot” | Default limit 25 MB (`UPLOAD_MAX_MB`) |
| Doc ends in **Fout** “geen laaibare tekstlaag” | Scanned PDF — v1 has no OCR; bring a text-layer PDF |
| App not reachable from LAN | Firewall: allow TCP **8090** inbound; the port is explicitly bound to `0.0.0.0` in `docker-compose.yml` |
| Slow first search | Model warm-up — normal; pre-warm with a test query |
| Toggled **Demo-modus** and results look weird | Mock vectors are keyword-ish; delete + re-upload documents after switching back to the real model |

> **Changing `EMBED_DIMS`** (vector size) requires a full reset (`down -v`), because existing
> vectors would have a different dimensionality.

## 8. Project layout

```
github-repo/
├── README.md                  ← this file (setup + demo runbook)
├── PLAN_WEBAPP_V1.md          ← full specification & decisions
├── docker-compose.yml         ← frontend + backend + qdrant (0.0.0.0:8090)
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

**Markdown is the only format downstream** (core design decision of the tooling doc): the v1 PDF
path stores a canonical Markdown file per document (`uploads/{doc_id}.md`, `## Page N` sections)
for inspection; adding video/audio/web sources later means adding a converter at the front —
zero changes to chunking, embedding, retrieval or summary.

## 9. Rehearsal checklist (the day before / morning of)

- [ ] Model system: `start-bge-m3.sh` (8081) + `start-qwen3-8b.sh` (8082) running, bound 0.0.0.0
- [ ] `docker compose up -d` on the demo server; all three containers healthy
- [ ] `http://<demo-server-ip>:8090` opens **from a second LAN device**
- [ ] Settings tab: IP entered → **Test verbinding** green for embedding + summary
- [ ] Header: 3 green dots (or amber *demo-modus* only if `EMBED_MOCK=1`)
- [ ] 2–3 verified text-layer KicMPi PDFs staged; **one pre-ingested** so the list isn't empty
- [ ] One full run of the demo script; pre-warm the models (one test search)
- [ ] **Screen recording of the rehearsal run saved** (worst-case fallback)
