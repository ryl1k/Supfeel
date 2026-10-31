# Per-app responsibility

> Status: **done** (Sprint 2). Paths below are real; keep them in sync with the code.

| App | Responsibility |
|---|---|
| backend | Owns the graph, state, checkpoints (Postgres), interrupts, event emission |
| frontend | Renders events; sends messages and confirmation decisions; holds no business logic |
| Neon DB | Persists conversations, messages, LangGraph checkpoints, action log |
| Claude API | understand / plan / respond reasoning only |
