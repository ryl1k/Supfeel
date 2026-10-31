# Data model

> Status: **done** (Sprint 2). Paths below are real; keep them in sync with the code.

| Table | Key columns |
|---|---|
| `conversations` | id (client uuid), customer_id, status (`open`/`awaiting_confirmation`/`resolved`/`escalated`), state jsonb |
| `messages` | id, conversation_id, role (`user`/`assistant`), content |
| `action_log` | id `ACT-…`, conversation_id, tool, args, result, status (`proposed`/`approved`/`declined`/`done`/`failed`), needs_confirmation, verified, verification |

`conversations.state`:
```json
{"previous": {"intent": {...}, "outcome": "asked", "pause_offered": false, "last_message": "..."},
 "pending":  {"intent": {...}, "facts": {...}, "policies": [...], "plan": {...}, "actions": [ActionRecord]}}
```
`ActionRecord`: action_id, tool, args, reason, title, description, amount_cents, needs_confirmation, status, result, error, verification.

SSE events: `step {step, status, detail, ...}`, `action_proposed {actions[]}`, `action_done {action}`,
`verified {action_id, title, ok, checks[]}`, `recommendations {provider, items[]}`, `token {text}`,
`notice {kind: fallback|budget, node, message}`, `error {code, message}`, `done {outcome, status, brain}`.
