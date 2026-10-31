# Per-app responsibility

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

| App | Responsibility |
|---|---|
| backend | Auth (passwords, sessions, principals, repo scoping), keys, price list, ledger, limits, mock cards |
| Neon DB | `accounts`, `users`, `user_sessions`, `api_keys`, `credit_entries`, `repos.account_id`, `llm_usage.account_id` |
| frontend | Login / signup forms, token in `localStorage`, session guard + balance pill in the shell, Billing page |
| payments | None: `mock_card` simulates a card; no money moves |
