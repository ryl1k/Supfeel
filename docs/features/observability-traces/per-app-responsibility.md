# Per-app responsibility

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

| App | Responsibility |
|---|---|
| backend | Create, nest and persist spans; attach cost; serve traces |
| Neon DB | `spans` table (indexed by `trace_id`) |
| frontend | `TraceView`: summary badges, flow graph per run, kind filters, waterfall, attribute panel |
