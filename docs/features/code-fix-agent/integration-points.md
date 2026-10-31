# Integration points

> Status: **done** (Sprint 5, updated in Sprint 6). Paths below are real; keep them in sync with the code.

- **ticket-resolution**: `fix_node` calls `investigate()` / `publish()` / `ci.track()`; merge calls `service.learn_ticket()`.
- **repo-indexing**: Workspace reads `repo_files`; `search_code` uses `search()`; the same `GitHub` client and App credentials.
- **llm-budget-guard**: `tool_turn(session_cap=FIX_CAP_USD, conversation_id=f"{ticket_id}:fix")`.
- **accounts-billing**: `fix_node` charges `fix` and refunds it on the `report` fallback.
- **mcp-server**: `ci.refresh` / `ci.on_pr_closed` call `callbacks.fire`; `relay()` exposes `engineering` (decision, root cause, PR, CI).
- **business-notifications**: `pr_opened`, `bug_reported`, `ci_passed`, `ci_failed`, `pr_merged`.
- **observability-traces**: agent turns are `llm` spans, tools are `tool` spans, GitHub calls `http` spans.
- GitHub App setup (permissions, webhook events): `docs/project/github-app-setup.md`.
