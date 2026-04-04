"""
FastAPI 應用程式 - 本地 RAG API
"""
from pathlib import Path
from typing import Any, Dict, List, Literal

from fastapi import FastAPI
from pydantic import BaseModel

from libs.utils import ensure_dirs
from libs.config import DATA_DIR, CACHE_PATH, TOP_K_RETRIEVE, TOP_K_FINAL
from services.chunking import load_all_markdown_files
from services.embedding import build_index_with_cache
from services.query import build_search_query
from services.retrieval import retrieve, rerank
from services.answer import answer_question

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
INDEX: List[Dict[str, Any]] = []


@app.on_event("startup")
def startup_event():
    global INDEX
    ensure_dirs(DATA_DIR, CACHE_PATH)
    chunks = load_all_markdown_files(DATA_DIR)
    INDEX = build_index_with_cache(chunks, CACHE_PATH)



@app.get("/health")
def health():
    return {"status": "ok", "chunks": len(INDEX)}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    search_query = build_search_query(req.query, req.mode)
    retrieved = retrieve(search_query, INDEX, top_k=TOP_K_RETRIEVE)
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
                path=x["path"],
                score=float(x["score"]),
            )
            for x in retrieved
        ],
        reranked=[
            RetrievedChunk(
                chunk_id=x["chunk_id"],
                source=x["source"],
                path=x["path"],
                score=float(x["score"]),
            )
            for x in reranked
        ],
        answer=answer,
    )