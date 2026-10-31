# Per-app responsibility

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

| App | Responsibility |
|---|---|
| backend | Ingest, embed, retrieve |
| Neon DB | `kb_chunks` with pgvector HNSW index, `embedding_cache` |
| OpenAI API | Embeddings only |
| frontend | Shows cited policy titles in the action trail (no retrieval logic) |
