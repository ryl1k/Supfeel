# Integration points

> Status: **done** (Sprint 5, updated in Sprint 6). Paths below are real; keep them in sync with the code.

- **llm-budget-guard**: summaries via `complete_text(session_cap=INDEX_CAP_USD, conversation_id="job:<id>")`, ask via `complete_json`.
- **knowledge-base-rag**: `app.rag.embeddings.embed()` / `active_model()` (shared `embedding_cache`).
- **ticket-resolution**: `support/context.py` calls `search()` over code/doc/summary/ticket/api chunks; `learn.py` writes `ticket` chunks.
- **assisted-actions**: consumes `api_operations` and `repos.settings.api_base_url` / `api_token`.
- **code-fix-agent**: reads `repo_files` (Workspace overlay), `search()`, and the shared `GitHub` client.
- **observability-traces**: every phase is a span; GitHub requests are `http` spans.
- **accounts-billing**: `repo_for` scoping, `index` / `ask` charges, `current_account` for AI-cost attribution.
- **mcp-server**: `get_product_overview` and `ask_product` read the index.
