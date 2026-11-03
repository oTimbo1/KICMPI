import os
import json
from urllib.request import Request, urlopen

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

import rag  # hergebruikt model, client en COLLECTION

app = FastAPI()


class Question(BaseModel):
    question: str
    k: int = 5


def retrieve(question: str, k: int):
    qvec = rag.model.encode(question, normalize_embeddings=True).tolist()
    hits = rag.client.query_points(rag.COLLECTION, query=qvec, limit=k).points
    return [{"score": round(h.score, 3), **h.payload} for h in hits]


def rank_files(hits):
    files = {}
    for h in hits:
        f = files.setdefault(
            h["source"],
            {"source": h["source"], "score": h["score"], "pages": set(), "best_chunk": h["text"]},
        )
        if h["score"] > f["score"]:
            f["score"], f["best_chunk"] = h["score"], h["text"]
        f["pages"].add(h["page"])
    ranked = sorted(files.values(), key=lambda f: -f["score"])
    for f in ranked:
        f["pages"] = sorted(f["pages"])
    return ranked


def generate(question: str, sources: list) -> str:
    context = "\n\n".join(
        f"[{i + 1}] ({s['source']}, p.{s['page']})\n{s['text']}"
        for i, s in enumerate(sources)
    )
    prompt = (
        "Beantwoord de vraag uitsluitend op basis van de context. "
        "Verwijs naar bronnen als [1], [2]. "
        "Staat het antwoord niet in de context, zeg dat dan.\n\n"
        f"Context:\n{context}\n\nVraag: {question}"
    )
    payload = json.dumps(
        {
            "model": os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
            "prompt": prompt,
            "stream": False,
        }
    ).encode("utf-8")
    request = Request(
        f"{os.getenv('OLLAMA_URL', 'http://localhost:11434').rstrip('/')}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=120) as response:
        result = json.load(response)
    return result["response"]


@app.post("/api/ask")
def ask(body: Question):
    hits = retrieve(body.question, 20)  # ruim zoeken voor de bestandsranking
    sources = hits[: body.k]
    return {
        "answer": generate(body.question, sources),
        "chunks": sources,
        "files": rank_files(hits),
    }


def pdf_path(name: str) -> Path:
    name = Path(name or "").name  # geen mappen in de bestandsnaam
    if not name.lower().endswith(".pdf"):
        raise HTTPException(400, "Alleen PDF-bestanden zijn toegestaan.")
    return rag.PDF_DIR / name


@app.get("/api/documents")
def documents():
    return [
        {
            "name": pdf.name,
            "size": pdf.stat().st_size,
            "modified": pdf.stat().st_mtime,
            "chunks": rag.count_chunks(pdf.name),
        }
        for pdf in sorted(rag.PDF_DIR.glob("*.pdf"), key=lambda p: p.name.lower())
    ]


@app.post("/api/documents")
def upload(file: UploadFile = File(...)):
    path = pdf_path(file.filename)
    data = file.file.read()
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, "Dit bestand is geen geldige PDF.")
    rag.PDF_DIR.mkdir(exist_ok=True)
    path.write_bytes(data)
    try:
        chunks = rag.index_pdf(path)
    except Exception as e:
        raise HTTPException(500, f"Indexeren mislukt: {e}")
    return {"name": path.name, "size": len(data), "chunks": chunks}


@app.get("/api/documents/{name}")
def download(name: str):
    path = pdf_path(name)
    if not path.exists():
        raise HTTPException(404, "Document niet gevonden.")
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@app.delete("/api/documents/{name}")
def delete(name: str):
    path = pdf_path(name)
    if not path.exists():
        raise HTTPException(404, "Document niet gevonden.")
    rag.remove_pdf(path.name)
    path.unlink()
    return {"deleted": path.name}


@app.get("/")
def index():
    return FileResponse("index.html")