CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id BIGSERIAL PRIMARY KEY,
    source_name TEXT NOT NULL,
    file_path TEXT,
    content_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source_name)
);

CREATE TABLE chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id TEXT NOT NULL,
    title TEXT,
    level INT,
    heading_path TEXT,
    part INT NOT NULL DEFAULT 1,
    text TEXT NOT NULL,
    text_hash TEXT NOT NULL,
    embedding VECTOR(768), -- 依你的 embedding model 維度調整
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, chunk_id)
);