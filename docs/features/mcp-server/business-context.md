# Business context

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

- One key = one repository (product) of one workspace. Keys are created in the repo's **Connect (MCP)** tab;
  the raw key (`sf_live_…`) is shown once. A revoked key fails every tool call.
- Tools and prices (`billing.PRICES`): `escalate` $0.15 per ticket (+ $1.00 if a fix run starts, refunded when
  Claude is unavailable), `ask_product` $0.02, `reply` / `confirm` included, `get_ticket`,
  `get_product_overview`, `list_tickets` free.
- `confirm` is annotated `destructive_hint=True` and may only carry the customer's explicit answer
  (`INSTRUCTIONS` and the tool docstring say so). It errors when the ticket is not `awaiting_confirmation`.
- Out of credit / monthly limit reached → a `ToolError` with the reason ("Monthly spend limit … resets on …",
  "Not enough credit …"), so the first-line agent can tell the customer a human will follow up.
- The handoff (`agent`, `attempted`, last 20 transcript messages) is stored on the ticket. Triage and the
  reply see it via `triage.handoff_block()` ("Do not repeat its answers").
- `customer_reply` follows the same rule as the web chat: no files, code, PRs or triage details (`RESPOND_SYSTEM`).
  PR / CI details go in `engineering` for the agent, not the customer.
- `callback_url` is accepted only if it starts with `https://` or `http://localhost` (max 500 chars).
