# Per-app responsibility

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

| App | Responsibility |
|---|---|
| backend | `/api/dashboard` aggregation (account-scoped), demo offer in `/api/github/status` |
| Neon DB | Reads `repos`, `tickets`, `ticket_actions`, `api_keys`, `credit_entries` (via billing summary) |
| frontend | Board, charts, wizard, motion, landing story and pricing; all charts are hand-built (no chart library) |
