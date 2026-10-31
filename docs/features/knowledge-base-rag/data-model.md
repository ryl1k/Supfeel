# Data model

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

| Table | Columns |
|---|---|
| `kb_chunks` | id, doc_id, heading, text, audience, tags text[], content_hash (unique, sha256 of model + text), embedding_model, embedding vector(1536), updated_at |
| `embedding_cache` | text_hash (pk), model, embedding vector(1536), created_at |

Index: `CREATE INDEX ON kb_chunks USING hnsw (embedding vector_cosine_ops);`
Enable once: `CREATE EXTENSION IF NOT EXISTS vector;`
