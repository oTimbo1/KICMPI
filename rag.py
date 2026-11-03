import os
import sys
import uuid
from pathlib import Path

import pymupdf as fitz
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, FieldCondition, Filter, FilterSelector, MatchValue, PointStruct, VectorParams,
)
from sentence_transformers import SentenceTransformer

COLLECTION = "docs"
PDF_DIR = Path("pdfs")
CHUNK_SIZE = 1000   # tekens
OVERLAP = 200
DIM = 1024          # bge-m3 dense dimensie

model = SentenceTransformer("BAAI/bge-m3")
client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))


def chunk_text(text: str):
    start = 0
    while start < len(text):
        yield text[start:start + CHUNK_SIZE]
        start += CHUNK_SIZE - OVERLAP


def load_pdf(path: Path):
    doc = fitz.open(path)
    for page_no, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        if text:
            yield page_no, text


def create_collection():
    client.create_collection(
        COLLECTION,
        vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
    )


def ensure_collection():
    if not client.collection_exists(COLLECTION):
        create_collection()


def pdf_records(pdf: Path):
    for page_no, text in load_pdf(pdf):
        for i, chunk in enumerate(chunk_text(text)):
            yield {"source": pdf.name, "page": page_no, "chunk": i, "text": chunk}


def upsert_records(records, show_progress=False):
    if not records:
        return
    vectors = model.encode(
        [r["text"] for r in records],
        batch_size=16,
        normalize_embeddings=True,
        show_progress_bar=show_progress,
    )
    points = [
        PointStruct(id=str(uuid.uuid4()), vector=v.tolist(), payload=r)
        for v, r in zip(vectors, records)
    ]
    for i in range(0, len(points), 100):
        client.upsert(COLLECTION, points=points[i:i + 100])


def source_filter(name: str):
    return Filter(must=[FieldCondition(key="source", match=MatchValue(value=name))])


def remove_pdf(name: str):
    """Verwijdert alle chunks van één PDF uit de collectie."""
    if client.collection_exists(COLLECTION):
        client.delete(COLLECTION, points_selector=FilterSelector(filter=source_filter(name)))


def index_pdf(pdf: Path) -> int:
    """(Her)indexeert één PDF zonder de rest van de collectie te raken."""
    ensure_collection()
    remove_pdf(pdf.name)
    records = list(pdf_records(pdf))
    upsert_records(records)
    return len(records)


def count_chunks(name: str) -> int:
    if not client.collection_exists(COLLECTION):
        return 0
    return client.count(COLLECTION, count_filter=source_filter(name), exact=True).count


def ingest():
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    create_collection()

    records = []
    for pdf in sorted(PDF_DIR.glob("*.pdf")):
        records.extend(pdf_records(pdf))

    print(f"{len(records)} chunks embedden...")
    upsert_records(records, show_progress=True)
    print("Klaar.")


def ask(question: str, k: int = 5):
    qvec = model.encode(question, normalize_embeddings=True).tolist()
    hits = client.query_points(COLLECTION, query=qvec, limit=k).points
    for h in hits:
        p = h.payload
        print(f"\n[{h.score:.3f}] {p['source']} (p.{p['page']})")
        print(p["text"][:300].replace("\n", " ") + "...")


def sources(topic: str, k: int = 20):
    qvec = model.encode(topic, normalize_embeddings=True).tolist()
    hits = client.query_points(COLLECTION, query=qvec, limit=k).points
    best = {}
    for h in hits:
        src = h.payload["source"]
        best[src] = max(best.get(src, 0), h.score)
    for src, score in sorted(best.items(), key=lambda x: -x[1]):
        print(f"{score:.3f}  {src}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "ingest":
        ingest()
    elif cmd == "ask":
        ask(" ".join(sys.argv[2:]))
    elif cmd == "sources":
        sources(" ".join(sys.argv[2:]))
    else:
        print('Gebruik: python rag.py ingest | ask "vraag" | sources "onderwerp"')