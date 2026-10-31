# Per-app responsibility

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

| App | Responsibility |
|---|---|
| backend | Ingest, embed, retrieve |
| Neon DB | `kb_chunks` with pgvector HNSW index, `embedding_cache` |
| OpenAI API | Embeddings only |
| frontend | Shows cited policy titles in the action trail (no retrieval logic) |
