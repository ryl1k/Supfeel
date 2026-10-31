# Known gotchas

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

- Dates in fixtures are **relative** ("delivered_days_ago": 9), resolved at seed time — otherwise the demo rots.
- Tool definitions must be emitted in a stable order or the prompt cache breaks.
- Use cents everywhere; format money only at the edges.
- Neon free compute scales to zero — first request after idle has ~1 s cold start; reset endpoint warms it.
- Write tools must be idempotent per `action_id` (retries after verify failure must not double-refund).
