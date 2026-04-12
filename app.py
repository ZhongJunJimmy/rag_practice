"""
FastAPI 應用程式 - 本地 RAG API
"""
from pathlib import Path
from typing import Any, Dict, List, Literal

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from libs.config import DATA_DIR, TOP_K_RETRIEVE, TOP_K_FINAL
from services.chunking import load_all_markdown_files
from services.query import build_search_query
from services.retrieval import rerank
from services.answer import answer_question
from services.embedding import embed_text
from services.storage import (
    upsert_document,
    get_existing_chunk_state,
    upsert_chunk_with_embedding,
    search_similar_chunks,
)
import hashlib
import shutil
import os

UPLOAD_DIR = DATA_DIR
ALLOWED_EXT = [".pdf", ".md"]

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


app = FastAPI(title="Local RAG API")


# =========================
# Request / Response Models
# =========================
class AskRequest(BaseModel):
    query: str
    mode: Literal["none", "rewrite", "hyde"] = "none"


class RetrievedChunk(BaseModel):
    chunk_id: str
    source: str
    path: str
    score: float


class AskResponse(BaseModel):
    query: str
    mode: str
    search_query: str
    retrieved: List[RetrievedChunk]
    reranked: List[RetrievedChunk]
    answer: str


# =========================
# Startup
# =========================



@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    search_query = build_search_query(req.query, req.mode)
    query_embedding = embed_text(search_query)
    retrieved = search_similar_chunks(query_embedding, top_k=TOP_K_RETRIEVE)
    reranked = rerank(req.query, retrieved, top_k=TOP_K_FINAL)
    answer = answer_question(req.query, reranked)

    return AskResponse(
        query=req.query,
        mode=req.mode,
        search_query=search_query,
        retrieved=[
            RetrievedChunk(
                chunk_id=x["chunk_id"],
                source=x["source"],
                path=x["file_path"],
                score=float(x["score"]),
            )
            for x in retrieved
        ],
        reranked=[
            RetrievedChunk(
                chunk_id=x["chunk_id"],
                source=x["source"],
                path=x["file_path"],
                score=float(x["score"]),
            )
            for x in reranked
        ],
        answer=answer,
    )

@app.post("/reindex")
def reindex():
    chunks = load_all_markdown_files(DATA_DIR)
    grouped = {}
    for chunk in chunks:
        grouped.setdefault(chunk["source"], []).append(chunk)

    total = 0
    inserted_or_updated = 0
    skipped = 0

    for source, source_chunks in grouped.items():
        full_text = "\n".join(c["text"] for c in source_chunks)
        document_hash = sha256_text(full_text)

        doc_id = upsert_document(
            source_name=source,
            file_path=source,
            content_hash=document_hash,
        )

        for chunk in source_chunks:
            total += 1
            text_hash = sha256_text(chunk["text"])

            existing = get_existing_chunk_state(doc_id, chunk["chunk_id"])

            if existing and existing["text_hash"] == text_hash:
                skipped += 1
                print(f"[SKIP] unchanged chunk: {chunk['chunk_id']}")
                continue

            emb = embed_text(chunk["text"])
            upsert_chunk_with_embedding(doc_id, chunk, emb, text_hash)

            inserted_or_updated += 1
            if existing:
                print(f"[UPDATE] changed chunk: {chunk['chunk_id']}")
            else:
                print(f"[INSERT] new chunk: {chunk['chunk_id']}")

    return {"status": "ok", "total": total, "inserted_or_updated": inserted_or_updated, "skipped": skipped}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        return {"error": "Invalid file type"}
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return JSONResponse({
        "filename": file.filename,
        "content_type": file.content_type,
        "saved_path": file_path
    })