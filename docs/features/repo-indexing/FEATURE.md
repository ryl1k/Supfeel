# Repository indexing

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

A business imports a GitHub repository (or a local directory in dev). Supfeel downloads one snapshot, chunks
code and docs, embeds them into pgvector, discovers the business API from an OpenAPI spec, and writes an
"explain everything" overview plus one summary per module. Push webhooks re-index incrementally.

## Why
Every other feature depends on it: ticket triage and explanations need the code and docs, assisted actions
need the API operations, and the fix agent reads and edits the indexed files.

## Scope
- In: import, snapshot download and filtering, chunking and outlines, embeddings, OpenAPI discovery,
  module and overview summaries, incremental re-index, search, repo Q&A (`/ask`), file browser API,
  per-repo settings (business API URL/token, spec URL, auto-fix, business name).
- Out: ticket handling (`ticket-resolution`), the fix PR flow (`code-fix-agent`), the generic
  embedding/budget client (`llm-budget-guard`, `knowledge-base-rag`).

## Success criteria
- One tarball request per job; unchanged files are never re-embedded; unchanged modules are never re-summarized.
- Works with no API keys (`LLM_MODE=mock`): mock embeddings + rule-built summaries.
- Each index job is a trace (`trace_id` = job id) visible in the dashboard.
