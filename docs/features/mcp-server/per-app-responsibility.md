# Per-app responsibility

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

| App | Responsibility |
|---|---|
| backend | `/mcp` endpoint, key auth, tools, progress, relay view, callbacks |
| Neon DB | `api_keys` (hash, `last_used_at`), `tickets.channel = "mcp"`, `tickets.meta`, `frontline` rows in `ticket_messages` |
| first-line agent (the business's) | Calls the tools, relays `customer_reply`, asks the confirmation question, receives callbacks |
| frontend | Connect tab: endpoint, key create/revoke, config snippets per client, tool list with prices |
