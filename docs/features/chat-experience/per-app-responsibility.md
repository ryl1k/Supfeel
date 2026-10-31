# Per-app responsibility

> Status: **done** (Sprint 3). Paths below are real; keep them in sync with the code.

| App | Responsibility |
|---|---|
| frontend | All rendering, SSE parsing, optimistic user message, reconnect |
| backend | Emits ordered events; owns all decisions |
