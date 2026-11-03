import os

from fastapi import FastAPI
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


LLM_BASE_URL = os.getenv("LLM_BASE_URL")          # bv. http://localhost:11434/v1
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")


def generate(question: str, sources: list):
    if not LLM_BASE_URL:
        return None  # alleen retrieval
    from openai import OpenAI

    context = "\n\n".join(
        f"[{i + 1}] ({s['source']}, p.{s['page']})\n{s['text']}"
        for i, s in enumerate(sources)
    )
    client = OpenAI(base_url=LLM_BASE_URL, api_key=os.getenv("LLM_API_KEY", "ollama"))
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        max_tokens=1000,
        messages=[
            {
                "role": "system",
                "content": (
                    "Beantwoord de vraag uitsluitend op basis van de context. "
                    "Antwoord in het Nederlands. "
                    "Verwijs naar bronnen als [1], [2]. "
                    "Staat het antwoord niet in de context, zeg dat dan."
                ),
            },
            {"role": "user", "content": f"Context:\n{context}\n\nVraag: {question}"},
        ],
    )
    return resp.choices[0].message.content


@app.post("/api/ask")
def ask(body: Question):
    hits = retrieve(body.question, 20)  # ruim zoeken voor de bestandsranking
    return {
        "answer": generate(body.question, hits[: body.k]), # alleen top-k naar Claude
        "files": rank_files(hits),
    }


@app.get("/")
def index():
    return FileResponse("index.html")