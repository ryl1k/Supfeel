# Known gotchas

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

- `EventSource` only supports GET — use `fetch` + ReadableStream parser for POST SSE.
- Railway/Vercel proxies may buffer: send `X-Accel-Buffering: no` and heartbeat comments every 15 s.
- `backdrop-filter` is expensive — one glass layer, don't nest.
- Use `mock` LLM mode while building UI to avoid spending budget.
