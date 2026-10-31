# Integration points

> Status: **done** (Sprint 2). Paths below are real; keep them in sync with the code.

- **llm-budget-guard**: every LLM call via `app.llm.client.complete()` / `stream()`; never the SDK directly.
- **business-tools**: `app.tools.registry.call(name, args)`; verifiers in `verify.py` use read tools.
- **knowledge-base-rag**: `app.rag.retrieve(query, k)` → chunks with `doc_id`, `heading`, `text`.
- **chat-experience**: event schema (`events.py` ↔ `frontend/lib/types.ts`).
- **Qloo (optional)**: via `business-tools` `get_recommendations`; agent must work when it is absent.
