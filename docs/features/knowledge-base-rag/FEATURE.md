# Knowledge base RAG

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

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
