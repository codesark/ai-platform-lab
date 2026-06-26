-- Schema for the RAG corpus. Auto-applied by docker-compose on first DB start.
-- NOTE: VECTOR(768) must match EMBEDDING_DIM (text-embedding-004 = 768).
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    doc_id     TEXT        NOT NULL,
    chunk_id   INT         NOT NULL,
    source     TEXT        NOT NULL,
    text       TEXT        NOT NULL,
    embedding  VECTOR(768) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (doc_id, chunk_id)
);

-- HNSW index for cosine distance. For large corpora, build the index AFTER the
-- bulk load; fine to pre-create here for a small seed set.
CREATE INDEX IF NOT EXISTS documents_embedding_hnsw
    ON documents USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
