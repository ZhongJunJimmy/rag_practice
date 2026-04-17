"""
FastAPI 應用程式 - 本地 RAG API
"""
from pathlib import Path
from typing import Any, Dict, List, Literal

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from libs.config import DATA_DIR, TOP_K_RETRIEVE, TOP_K_FINAL
from services.chunking import load_all_files
from services.query import build_search_query
from services.retrieval import rerank
from services.answer import answer_question
from services.embedding import embed_text
from services.storage import (
    upsert_document,
    get_existing_chunk_state,
    upsert_chunk_with_embedding,
    search_similar_chunks,
    add_user,
    delete_user,
    get_all_users,
    add_group,
    update_group,
    get_group,
    get_all_groups,
    delete_group,
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
    user_id: str = None

class UserRequest(BaseModel):
    user_id: str
    username: str

class GroupRequest(BaseModel):
    group_id: str
    group_name: str
    users_id: List[str]

class DocumentGroupRequest(BaseModel):
    source_name: str
    groups: List[str]


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
    search_queries = build_search_query(req.query, req.mode)
    
    # 針對每個改寫後的查詢進行檢索並聚合結果
    all_retrieved = []
    for sq in search_queries:
        q_emb = embed_text(sq)
        res = search_similar_chunks(sq, q_emb, top_k=TOP_K_RETRIEVE, user_id=req.user_id)
        all_retrieved.extend(res)
    
    # 根據 chunk_id 去重 (保留第一次出現的結果)
    seen_ids = set()
    unique_retrieved = []
    for item in all_retrieved:
        if item["chunk_id"] not in seen_ids:
            unique_retrieved.append(item)
            seen_ids.add(item["chunk_id"])
            
    reranked = rerank(req.query, unique_retrieved, top_k=TOP_K_FINAL)
    answer = answer_question(req.query, reranked)

    return AskResponse(
        query=req.query,
        mode=req.mode,
        search_query="\n".join(search_queries),
        retrieved=[
            RetrievedChunk(
                chunk_id=x["chunk_id"],
                source=x["source"],
                path=x["file_path"],
                score=float(x["score"]),
            )
            for x in unique_retrieved
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
    chunks = load_all_files(DATA_DIR)
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

            emb = embed_text(chunk["text"]) if not chunk.get("is_parent") else None
            upsert_chunk_with_embedding(doc_id, chunk, emb, text_hash)

            inserted_or_updated += 1
            if existing:
                print(f"[UPDATE] changed chunk: {chunk['chunk_id']}")
            else:
                print(f"[INSERT] new chunk: {chunk['chunk_id']}")

    return {"status": "ok", "total": total, "inserted_or_updated": inserted_or_updated, "skipped": skipped}

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    filename: str = Form(...),
    password: str = Form(None),
    user_id: str = Form(None)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        return {"error": "Invalid file type"}
    
    save_name = filename
    file_path = os.path.join(UPLOAD_DIR, save_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Calculate file hash for document tracking
    with open(file_path, "rb") as f:
        file_bytes = f.read()
        content_hash = hashlib.sha256(file_bytes).hexdigest()

    # Store document, password, and user in DB
    upsert_document(
        source_name=filename,
        file_path=file_path,
        content_hash=content_hash,
        password=password,
        update_user_id=user_id
    )

    return JSONResponse({
        "filename": filename,
        "content_type": file.content_type,
        "saved_path": file_path,
        "password_stored": password is not None,
        "user_id_stored": user_id is not None
    })

@app.post("/addUser")
def add_user_api(req: UserRequest):
    print(f"Attempting to add user: {req.user_id} ({req.username})")
    success = add_user(req.user_id, req.username)
    if success:
        return {"status": "ok", "message": f"User {req.user_id} added successfully"}
    else:
        return JSONResponse(status_code=400, content={"status": "error", "message": "User already exists or could not be added"})

@app.post("/delUser")
def del_user_api(req: UserRequest):
    success = delete_user(req.user_id)
    if success:
        return {"status": "ok", "message": f"User {req.user_id} deleted successfully"}
    else:
        return JSONResponse(status_code=400, content={"status": "error", "message": "User not found or could not be deleted"})

@app.get("/getUsers")
async def list_users_api():
    print("Fetching all users...")
    success, users = get_all_users()
    print(f"Retrieved users: {users}")
    if success:
        return {"status": "ok", "users": users}
    else:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Could not retrieve users"})

@app.post("/addGroup")
def add_group_api(req: GroupRequest):
    success = add_group(req.group_id, req.group_name, req.users_id)
    if success:
        return {"status": "ok", "message": f"Group {req.group_id} added successfully"}
    else:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Could not add group"})

@app.put("/updateGroup")
def update_group_api(req: GroupRequest):
    success = update_group(req.group_id, req.group_name, req.users_id)
    if success:
        return {"status": "ok", "message": f"Group {req.group_id} updated successfully"}
    else:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Group not found or could not be updated"})

@app.get("/getGroup")
def get_group_api(group_id: str):
    success, group = get_group(group_id)
    if success and group:
        return {"status": "ok", "group": group}
    elif success:
        return JSONResponse(status_code=404, content={"status": "error", "message": "Group not found"})
    else:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Could not retrieve group"})

@app.get("/getGroups")
def get_all_groups_api():
    success, groups = get_all_groups()
    if success:
        return {"status": "ok", "groups": groups}
    else:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Could not retrieve groups"})

@app.delete("/delGroup")
def del_group_api(group_id: str):
    success = delete_group(group_id)
    if success:
        return {"status": "ok", "message": f"Group {group_id} deleted successfully"}
    else:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Group not found or could not be deleted"})

from services.storage import update_document_groups

@app.put("/updateDocumentGroups")
def update_doc_groups_api(req: DocumentGroupRequest):
    success = update_document_groups(req.source_name, req.groups)
    if success:
        return {"status": "ok", "message": f"Groups for document {req.source_name} updated successfully"}
    else:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Document not found or could not update groups"})
