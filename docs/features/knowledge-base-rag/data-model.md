# Data model

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

| Table | Columns |
|---|---|
| `kb_chunks` | id, doc_id, heading, text, audience, tags text[], content_hash (unique), embedding vector(1536), updated_at |
| `embedding_cache` | text_hash (pk), embedding vector(1536), created_at |

Index: `CREATE INDEX ON kb_chunks USING hnsw (embedding vector_cosine_ops);`
Enable once: `CREATE EXTENSION IF NOT EXISTS vector;`
