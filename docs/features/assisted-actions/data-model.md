# Data model

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

| Table | Key columns |
|---|---|
| `ticket_actions` | id (`act_<hex>`), ticket_id, operation_id, method, path, args JSONB `{path, query, body}`, title, status (`proposed`/`approved`/`declined`/`done`/`failed`), needs_confirmation, response JSONB `{status, data}`, verification JSONB `{ok, checks: [{name, ok, detail}]}`, created_at |
| `api_operations` | see `repo-indexing` |
| `tickets.state` | `{pending_action: {...}}` while `awaiting_confirmation` |

The `why` of a proposal is kept in graph state / `pending_action` but not stored in `ticket_actions`.
