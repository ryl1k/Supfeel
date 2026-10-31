# Known gotchas

> Status: **done** (Sprint 3). Paths below are real; keep them in sync with the code.

- `EventSource` only supports GET — use `fetch` + ReadableStream parser for POST SSE.
- Railway/Vercel proxies may buffer: send `X-Accel-Buffering: no` and heartbeat comments every 15 s.
- `backdrop-filter` is expensive — one glass layer, don't nest.
- Use `mock` LLM mode while building UI to avoid spending budget.
- Reloading the page loses the visible transcript (client state). The backend still has it at `GET /api/conversations/{id}`. Restoring it is a possible improvement.
- A typed message while a proposal is open supersedes it (the backend declines it too), so the card shows "Superseded".
- The backend's CORS_ORIGINS must include the frontend origin (Vercel URL in prod).
