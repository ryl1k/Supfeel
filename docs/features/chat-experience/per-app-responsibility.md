# Per-app responsibility

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

| App | Responsibility |
|---|---|
| frontend | All rendering, SSE parsing, optimistic user message, reconnect |
| backend | Emits ordered events; owns all decisions |
