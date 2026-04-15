# services/storage.py
import hashlib
from libs.db import get_conn, put_conn

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def upsert_document(source_name: str, file_path: str, content_hash: str) -> int:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO documents (source_name, file_path, content_hash)
                VALUES (%s, %s, %s)
                ON CONFLICT (source_name)
                DO UPDATE SET
                    file_path = EXCLUDED.file_path,
                    content_hash = EXCLUDED.content_hash,
                    updated_at = NOW()
                RETURNING id
            """, (source_name, file_path, content_hash))
            return cur.fetchone()[0]
    finally:
        put_conn(conn)

def upsert_chunk_with_embedding(document_id: int, chunk: dict, embedding: list[float], text_hash: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Resolve parent_id if this is a child chunk
            parent_id = None
            parent_chunk_id = chunk.get("parent_chunk_id")
            if parent_chunk_id:
                cur.execute("SELECT id FROM chunks WHERE document_id = %s AND chunk_id = %s", (document_id, parent_chunk_id))
                row = cur.fetchone()
                if row:
                    parent_id = row[0]

            cur.execute("""
                INSERT INTO chunks (
                    document_id, chunk_id, title, level, heading_path,
                    part, text, text_hash, embedding, parent_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id, chunk_id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    level = EXCLUDED.level,
                    heading_path = EXCLUDED.heading_path,
                    part = EXCLUDED.part,
                    text = EXCLUDED.text,
                    text_hash = EXCLUDED.text_hash,
                    embedding = EXCLUDED.embedding,
                    parent_id = EXCLUDED.parent_id,
                    updated_at = NOW()
            """, (
                document_id,
                chunk["chunk_id"],
                chunk.get("title"),
                chunk.get("level"),
                chunk.get("heading_path"),
                chunk.get("part", 1),
                chunk["text"],
                text_hash,
                embedding,
                parent_id,
            ))
    finally:
        put_conn(conn)

def upsert_chunk(document_id: int, chunk: dict, embedding: list[float]):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Resolve parent_id if this is a child chunk
            parent_id = None
            parent_chunk_id = chunk.get("parent_chunk_id")
            if parent_chunk_id:
                cur.execute("SELECT id FROM chunks WHERE document_id = %s AND chunk_id = %s", (document_id, parent_chunk_id))
                row = cur.fetchone()
                if row:
                    parent_id = row[0]

            cur.execute("""
                INSERT INTO chunks (
                    document_id, chunk_id, title, level, heading_path,
                    part, text, text_hash, embedding, parent_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id, chunk_id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    level = EXCLUDED.level,
                    heading_path = EXCLUDED.heading_path,
                    part = EXCLUDED.part,
                    text = EXCLUDED.text,
                    text_hash = EXCLUDED.text_hash,
                    embedding = EXCLUDED.embedding,
                    parent_id = EXCLUDED.parent_id,
                    updated_at = NOW()
            """, (
                document_id,
                chunk["chunk_id"],
                chunk.get("title"),
                chunk.get("level"),
                chunk.get("heading_path"),
                chunk.get("part", 1),
                chunk["text"],
                sha256_text(chunk["text"]),
                embedding,
                parent_id,
            ))
    finally:
        put_conn(conn)

def count_chunks() -> int:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM chunks")
            return cur.fetchone()[0]
    finally:
        put_conn(conn)

def search_similar_chunks(query_text: str, query_embedding: list[float], top_k: int = 5):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # 使用 Hybrid Search: 結合 pgvector 語意搜尋與 PostgreSQL Full Text Search (Keyword)
            # 我們使用 websearch_to_tsquery 以支援更靈活的關鍵字查詢 (類似 Google 搜尋)
            # 由於沒有預先建立 tsvector 索引，這裡在查詢時動態產生，適用於中小型數據集
            cur.execute("""
                WITH semantic_search AS (
                    SELECT 
                        c.id, 
                        1 - (c.embedding <=> %s::vector) AS score
                    FROM chunks c
                    WHERE c.embedding IS NOT NULL
                    ORDER BY c.embedding <=> %s::vector
                    LIMIT %s
                ),
                keyword_search AS (
                    SELECT 
                        c.id, 
                        ts_rank(to_tsvector('english', c.text), websearch_to_tsquery('english', %s)) AS score
                    FROM chunks c
                    WHERE to_tsvector('english', c.text) @@ websearch_to_tsquery('english', %s)
                    ORDER BY score DESC
                    LIMIT %s
                ),
                combined AS (
                    SELECT id, score FROM semantic_search
                    UNION ALL
                    SELECT id, score FROM keyword_search
                )
                SELECT 
                    c.id,
                    c.chunk_id,
                    c.title,
                    c.level,
                    c.heading_path,
                    c.part,
                    COALESCE(p.text, c.text) as text,
                    d.source_name,
                    d.file_path,
                    MAX(comb.score) as score
                FROM combined comb
                JOIN chunks c ON comb.id = c.id
                LEFT JOIN chunks p ON c.parent_id = p.id
                JOIN documents d ON c.document_id = d.id
                GROUP BY c.id, c.chunk_id, c.title, c.level, c.heading_path, c.part, p.text, c.text, d.source_name, d.file_path
                ORDER BY score DESC
                LIMIT %s
            """, (query_embedding, query_embedding, top_k * 2, query_text, query_text, top_k * 2, top_k))

            rows = cur.fetchall()

            results = []
            for row in rows:
                results.append({
                    "id": row[0],
                    "chunk_id": row[1],
                    "title": row[2],
                    "level": row[3],
                    "heading_path": row[4],
                    "part": row[5],
                    "text": row[6],
                    "source": row[7],
                    "file_path": row[8],
                    "score": float(row[9]),
                })
            return results
    finally:
        put_conn(conn)

# services/storage.py
from libs.db import get_conn, put_conn

def get_existing_chunk_state(document_id: int, chunk_id: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, text_hash
                FROM chunks
                WHERE document_id = %s AND chunk_id = %s
            """, (document_id, chunk_id))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "text_hash": row[1],
            }
    finally:
        put_conn(conn)

