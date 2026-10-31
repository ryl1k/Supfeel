# Integration points

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

- **llm-budget-guard**: every LLM call via `app.llm.client.complete()` / `stream()`; never the SDK directly.
- **business-tools**: `app.tools.registry.call(name, args)`; verifiers in `verify.py` use read tools.
- **knowledge-base-rag**: `app.rag.retrieve(query, k)` → chunks with `doc_id`, `heading`, `text`.
- **chat-experience**: event schema (`events.py` ↔ `frontend/lib/types.ts`).
- **Qloo (optional)**: via `business-tools` `get_recommendations`; agent must work when it is absent.
