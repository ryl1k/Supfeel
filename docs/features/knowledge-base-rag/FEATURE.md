# Knowledge base RAG

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

Retrieves Velora policy and FAQ chunks so the agent's decisions are grounded in written policy
and can cite it.

## Why
Prevents invented policy; makes decisions explainable ("per the 30-day comfort guarantee…").

## Scope
- In: chunking `knowledge-base/**/*.md` by `##`, embedding with `text-embedding-3-small`,
  storing in pgvector, top-k retrieval, embedding cache.
- Out: authoring policy content (lives in `knowledge-base/`).

## Success criteria
- Hero query returns the comfort-guarantee chunk in top 3.
- Full re-ingest costs < $0.01; unchanged chunks are never re-embedded.
