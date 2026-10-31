# Integration points

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- **llm-budget-guard**: `ledger.record(annotate=True)` → `annotate_usage`; `stream_text` passes cost to `record_span` instead.
- **knowledge-base-rag**: `embed()` opens an `embedding` span only for real OpenAI calls (mock embeddings are untraced).
- **repo-indexing**, **ticket-resolution**, **assisted-actions**, **code-fix-agent**, **business-notifications**: all open spans.
- Frontend pages: ticket detail, repo Index runs and Ask tabs.
