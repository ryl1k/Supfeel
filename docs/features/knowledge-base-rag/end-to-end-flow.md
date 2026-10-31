# End-to-end flow

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

**Ingest** (`python -m app.rag.ingest`):
1. Walk `knowledge-base/`, parse frontmatter, split on `##` → chunks `{doc_id, heading, text, audience, tags}`.
2. `sha256(text)` per chunk; skip if hash already in `kb_chunks`.
3. Batch-embed new chunks (one OpenAI request), upsert; delete chunks whose doc no longer has them.

**Retrieve** (`retrieve(query, k=5)`):
1. Embed query (cache hit → no API call).
2. `ORDER BY embedding <=> :q LIMIT k`, filter by audience if needed.
3. Return chunks + cosine score.
