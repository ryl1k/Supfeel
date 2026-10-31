# Data model

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

| Table | Key columns used here |
|---|---|
| `api_keys` | id (`key_<hex>`), account_id, repo_id, name, prefix (first 14 chars), key_hash (sha256, unique), last_used_at, revoked |
| `tickets` | channel (`mcp` for escalations), meta JSONB `{handoff: {agent, attempted, transcript}, key_id, callback_url?}` |
| `ticket_messages` | role `frontline` for the first-line agent's transcript lines (plus `customer`, `agent`) |
| `spans` | `callback <event>` (`kind="http"`, trace_id = ticket id) |

Relay view (`service.relay`, not stored): `ticket_id, status, category, customer_reply, next_step, trace_url,
needs_confirmation?, engineering?`. Callback body: `{"event": <status>, "ticket": <relay view>}`.
