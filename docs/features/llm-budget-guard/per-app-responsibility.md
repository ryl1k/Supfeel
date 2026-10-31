# Per-app responsibility

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

| App | Responsibility |
|---|---|
| backend | Everything in this feature |
| Neon DB | `llm_usage` ledger (survives redeploys) |
| frontend | Shows a friendly message on `budget_exceeded` event; optional usage badge in dev |
