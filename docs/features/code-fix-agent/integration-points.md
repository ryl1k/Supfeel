# Integration points

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- **ticket-resolution**: `fix_node` calls `investigate()` / `publish()` / `ci.track()`; merge calls `service.learn_ticket()`.
- **repo-indexing**: Workspace reads `repo_files`; `search_code` uses `search()`; the same `GitHub` client and App credentials.
- **llm-budget-guard**: `tool_turn(session_cap=FIX_CAP_USD, conversation_id=ticket_id)`.
- **business-notifications**: `pr_opened`, `bug_reported`, `ci_passed`, `ci_failed`, `pr_merged`.
- **observability-traces**: agent turns are `llm` spans, tools are `tool` spans, GitHub calls `http` spans.
- GitHub App setup (permissions, webhook events): `docs/project/github-app-setup.md`.
