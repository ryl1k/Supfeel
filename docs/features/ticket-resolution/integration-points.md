# Integration points

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- **repo-indexing**: `search()` for context; `learn()` writes `ticket` chunks into `repo_chunks`.
- **assisted-actions**: `assist_node` → `assist.plan()` / `propose()`; `act_node` → `assist.execute()`.
- **code-fix-agent**: `fix_node` → `fixer.investigate()` / `publish()`, then `ci.track()`; `ci.on_pr_closed()` calls `service.learn_ticket()`.
- **business-notifications**: `notify()` from feature, escalate, assist, act, fix nodes and on crashes.
- **llm-budget-guard**: `complete_json` / `stream_text` / `tool_turn` with `session_cap` and `conversation_id=ticket_id`.
- **observability-traces**: one `run` span per turn, one `step` span per node (`traced()`).
