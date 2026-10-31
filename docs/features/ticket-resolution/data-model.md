# Data model

> Status: **done** (Sprint 5, updated in Sprint 6). Paths below are real; keep them in sync with the code.

| Table | Key columns |
|---|---|
| `tickets` | id (`T-XXXXXX`), repo_id, customer JSONB `{name, email, ref}`, channel (`web`/`mcp`), meta JSONB `{handoff: {agent, attempted, transcript}, callback_url, key_id}` (MCP only), subject, category, confidence, status, triage JSONB (+route, brain), resolution JSONB, fix JSONB, state JSONB (`pending_action`), learned, created_at, updated_at |
| `ticket_messages` | ticket_id, role (`customer`/`agent`/`frontline`/`system`), content, created_at |
| `repo_chunks` (kind `ticket`) | path = ticket id, text = `learn.ticket_text()` |

`TicketState` (`support/state.py`) is the in-graph state: ticket_id, repo_id, business, customer, mode
(`message`/`confirm`), approved, account_id, handoff, message, history, ctx, triage, brain (node → `llm`/`rules`), route, action,
fix, status, resolution, notes, reply. Nothing is checkpointed by LangGraph: `_finish` writes the outcome to `tickets`.
Related: `ticket_actions` (assisted-actions), `notifications` (business-notifications), `spans` (observability-traces).
