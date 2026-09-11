-- =========================================================================
-- Lost & Found Agent — database schema (PostgreSQL + pgvector)
--
-- Run once against the target database, e.g.:
--   psql "$DATABASE_URL" -f sql/schema.sql
--
-- The embedding column dimension (384) MUST match EMBEDDING_DIM in .env and the
-- output of app/embeddings.py (all-MiniLM-L6-v2 -> 384).
-- =========================================================================

-- Enable pgvector (safe to re-run).
CREATE EXTENSION IF NOT EXISTS vector;

-- -------------------------------------------------------------------------
-- items: every lost or found report lives here.
--   kind        : 'lost' or 'found'
--   status      : 'open'      -> unmatched, searchable
--                 'matched'   -> confidently matched to a counterpart
--                 'escalated' -> low/ambiguous confidence, needs human review
--   embedding   : semantic vector of `raw_text`, used for pgvector RAG search
-- Structured fields are nullable because intake may not extract all of them.
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS items (
    id           BIGSERIAL PRIMARY KEY,
    kind         TEXT NOT NULL CHECK (kind IN ('lost', 'found')),
    status       TEXT NOT NULL DEFAULT 'open'
                 CHECK (status IN ('open', 'matched', 'escalated')),

    -- Structured fields extracted at intake.
    item_type    TEXT,
    color        TEXT,
    brand        TEXT,
    location     TEXT,
    reported_date DATE,

    -- Free-text report and its embedding.
    raw_text     TEXT NOT NULL,
    embedding    vector(384),

    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Filter helpers: most queries are "open items of the opposite kind".
CREATE INDEX IF NOT EXISTS items_kind_status_idx ON items (kind, status);

-- Approximate-nearest-neighbor index for cosine similarity search.
-- vector_cosine_ops pairs with the `<=>` cosine-distance operator used in
-- retrieval. IVFFlat needs ANALYZE after data is loaded to pick list counts;
-- for a small hackathon dataset this is plenty fast.
CREATE INDEX IF NOT EXISTS items_embedding_cosine_idx
    ON items USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
