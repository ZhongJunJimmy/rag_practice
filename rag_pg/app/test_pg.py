from __future__ import annotations

import psycopg
from pgvector.psycopg import register_vector

DB_URL = "postgresql://rag_user:rag_password@127.0.0.1:5432/rag_db"


def main() -> None:
    embedding = [0.1] * 384

    with psycopg.connect(DB_URL) as conn:
        register_vector(conn)

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (source, chunk_id, title, path, content, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (chunk_id) DO UPDATE SET
                    source = EXCLUDED.source,
                    title = EXCLUDED.title,
                    path = EXCLUDED.path,
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding
                """,
                (
                    "notes.md",
                    "notes_0001",
                    "RAG Overview",
                    "RAG Overview",
                    "RAG 是 Retrieval-Augmented Generation。",
                    embedding,
                ),
            )

        conn.commit()

    print("insert ok")


if __name__ == "__main__":
    main()