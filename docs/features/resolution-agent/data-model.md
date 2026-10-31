# Data model

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

| Table | Key columns |
|---|---|
| `conversations` | id, customer_id, status (`open`/`resolved`/`escalated`), created_at |
| `messages` | id, conversation_id, role, content, created_at |
| `action_log` | id, conversation_id, tool, input jsonb, output jsonb, status (`proposed`/`approved`/`done`/`failed`), verified bool |
| `checkpoints` | LangGraph Postgres checkpointer tables (managed by the library) |

`AgentState.plan` item: `{id, tool, args, reason, policy_ref, needs_confirmation}`.
