# Per-app responsibility

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

| App | Responsibility |
|---|---|
| backend | Everything in this feature |
| Neon DB | `llm_usage` ledger (survives redeploys) |
| frontend | Shows a friendly message on `budget_exceeded` event; optional usage badge in dev |
