# services/storage.py
import hashlib
from libs.db import get_conn, put_conn

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def upsert_document(source_name: str, file_path: str, content_hash: str, password: str = None, update_user_id: str = None) -> int:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO documents (source_name, file_path, content_hash, password, update_user_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (source_name)
                DO UPDATE SET
                    file_path = EXCLUDED.file_path,
                    content_hash = EXCLUDED.content_hash,
                    password = EXCLUDED.password,
                    update_user_id = EXCLUDED.update_user_id,
                    updated_at = NOW()
                RETURNING id
            """, (source_name, file_path, content_hash, password, update_user_id))
            return cur.fetchone()[0]
    finally:
        put_conn(conn)

def update_document_groups(source_name: str, groups: list[str]) -> bool:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE documents 
                SET groups = %s, updated_at = NOW() 
                WHERE source_name = %s
            """, (groups, source_name))
            return cur.rowcount > 0
    except Exception:
        return False
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

def get_user_groups(user_id: str) -> list[str]:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT group_id FROM groups WHERE %s = ANY(users_id)", (user_id,))
            rows = cur.fetchall()
            return [row[0] for row in rows]
    finally:
        put_conn(conn)

def search_similar_chunks(query_text: str, query_embedding: list[float], top_k: int = 5, user_id: str = None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # 獲取該用戶所屬的所有群組
            user_groups = get_user_groups(user_id) if user_id else []
            
            # 權限過濾條件
            # 如果有提供 user_id，則必須符合 (update_user_id == user_id OR groups 包含用戶所屬群組)
            filter_condition = ""
            filter_params = []
            if user_id:
                filter_condition = "AND (d.update_user_id = %s OR d.groups && %s)"
                filter_params = [user_id, user_groups]

            # 使用 Hybrid Search: 結合 pgvector 語意搜尋與 PostgreSQL Full Text Search (Keyword)
            cur.execute(f"""
                WITH semantic_search AS (
                    SELECT 
                        c.id, 
                        1 - (c.embedding <=> %s::vector) AS score
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE c.embedding IS NOT NULL
                    {filter_condition}
                    ORDER BY c.embedding <=> %s::vector
                    LIMIT %s
                ),
                keyword_search AS (
                    SELECT 
                        c.id, 
                        ts_rank(to_tsvector('english', c.text), websearch_to_tsquery('english', %s)) AS score
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE to_tsvector('english', c.text) @@ websearch_to_tsquery('english', %s)
                    {filter_condition}
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
            """, (
                query_embedding, *filter_params, query_embedding, top_k * 2, 
                query_text, *filter_params, query_text, top_k * 2, 
                top_k
            ))

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

def get_document_password(source_name: str) -> str | None:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT password FROM documents WHERE source_name = %s", (source_name,))
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        put_conn(conn)

def add_user(user_id: str, username: str) -> bool:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (user_id, username) VALUES (%s, %s)", (user_id, username))
            conn.commit()
            return True
    except Exception:
        conn.rollback()
        return False
    finally:
        put_conn(conn)

def delete_user(user_id: str) -> bool:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            conn.commit()
            return cur.rowcount > 0
    except Exception:
        conn.rollback()
        return False
    finally:
        put_conn(conn)

# return status, list of users
def get_all_users() -> tuple[bool, list[dict]]:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, username FROM users ORDER BY created_at")
            rows = cur.fetchall()
            return True, [{"user_id": row[0], "username": row[1]} for row in rows]
    except Exception:
        return False, []
    finally:
        put_conn(conn)

def add_group(group_id: str, group_name: str, users_id: list[str]) -> bool:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO groups (group_id, group_name, users_id) VALUES (%s, %s, %s)", (group_id, group_name, users_id))
            conn.commit()
            return True
    except Exception:
        conn.rollback()
        return False
    finally:
        put_conn(conn)

def update_group(group_id: str, group_name: str, users_id: list[str]) -> bool:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE groups SET group_name = %s, users_id = %s WHERE group_id = %s", (group_name, users_id, group_id))
            conn.commit()
            return cur.rowcount > 0
    except Exception:
        conn.rollback()
        return False
    finally:
        put_conn(conn)

def get_group(group_id: str) -> tuple[bool, dict | None]:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT group_id, group_name, users_id FROM groups WHERE group_id = %s", (group_id,))
            row = cur.fetchone()
            if row:
                return True, {"group_id": row[0], "group_name": row[1], "users_id": row[2]}
            return True, None
    except Exception:
        return False, None
    finally:
        put_conn(conn)

def get_all_groups() -> tuple[bool, list[dict]]:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT group_id, group_name, users_id FROM groups ORDER BY created_at")
            rows = cur.fetchall()
            return True, [{"group_id": row[0], "group_name": row[1], "users_id": row[2]} for row in rows]
    except Exception:
        return False, []
    finally:
        put_conn(conn)

def delete_group(group_id: str) -> bool:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM groups WHERE group_id = %s", (group_id,))
            conn.commit()
            return cur.rowcount > 0
    except Exception:
        conn.rollback()
        return False
    finally:
        put_conn(conn)
