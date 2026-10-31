# Data model

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

| Table | Columns |
|---|---|
| `spans` | id (uuid hex), trace_id (indexed), parent_id, name (≤ 120 chars, truncated), kind, status (`ok`/`error`), attributes JSONB, cost_usd numeric(12,6), started_at, ended_at, duration_ms |

Common attributes: `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, `model`,
`node`, `cached`, `input_preview`, `output`, `error`, `status` (HTTP), `query`, `results`.
