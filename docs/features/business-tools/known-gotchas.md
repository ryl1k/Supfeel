# Known gotchas

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

- Dates in fixtures are **relative** ("delivered_days_ago": 9), resolved at seed time — otherwise the demo rots.
- Tool definitions must be emitted in a stable order or the prompt cache breaks.
- Use cents everywhere; format money only at the edges.
- Neon free compute scales to zero — first request after idle has ~1 s cold start; reset endpoint warms it.
- Write tools must be idempotent per `action_id` (retries after verify failure must not double-refund).
- Exchange creates a new `VX-…` order immediately (advance exchange) and decrements stock; the return label is a separate tool call.
- `get_payments` flags `possible_duplicate_of` only for two **captured** payments; authorized holds are never duplicates.
- Customer scoping is enforced inside every tool via `ctx.customer_id`; never trust IDs from the model without it.
