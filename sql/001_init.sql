-- Schéma initial. Exécuté automatiquement au premier démarrage du conteneur PostgreSQL.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id          BIGSERIAL PRIMARY KEY,
    filename    TEXT NOT NULL UNIQUE,
    company     TEXT,
    fiscal_year INT,
    sha256      CHAR(64) NOT NULL,          -- pour l'ingestion incrémentale
    n_pages     INT,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE chunk_type AS ENUM ('text', 'table', 'figure');

CREATE TABLE IF NOT EXISTS chunks (
    id           BIGSERIAL PRIMARY KEY,
    document_id  BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_start   INT NOT NULL,
    page_end     INT NOT NULL,
    section      TEXT,
    content_type chunk_type NOT NULL DEFAULT 'text',
    content      TEXT NOT NULL,
    content_hash CHAR(64) NOT NULL,
    image_path   TEXT,                       -- pour les chunks de type figure
    metadata     JSONB NOT NULL DEFAULT '{}',
    embedding    vector(1024),               -- bge-m3 ; à changer avec le modèle
    tsv          tsvector GENERATED ALWAYS AS (to_tsvector('french', content)) STORED,
    CHECK (page_end >= page_start)
);

-- Recherche vectorielle approximative (distance cosinus)
CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw
    ON chunks USING hnsw (embedding vector_cosine_ops);

-- Recherche lexicale (pour la recherche hybride)
CREATE INDEX IF NOT EXISTS chunks_tsv_gin ON chunks USING gin (tsv);

CREATE INDEX IF NOT EXISTS chunks_document_id ON chunks (document_id);
