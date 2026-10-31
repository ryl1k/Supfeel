# Per-app responsibility

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

| App | Responsibility |
|---|---|
| backend | Owns the graph, state, checkpoints (Postgres), interrupts, event emission |
| frontend | Renders events; sends messages and confirmation decisions; holds no business logic |
| Neon DB | Persists conversations, messages, LangGraph checkpoints, action log |
| Claude API | understand / plan / respond reasoning only |
