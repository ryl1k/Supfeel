# End-to-end flow

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

**Message turn** (route `assist`, `graph.assist_node`):
1. `assist.plan()` (span "plan action"): no operations or no `api_base_url` → `cannot`.
2. Claude: `plan_llm()` tool loop (`tool_turn`, node `assist_plan`, cap `TICKET_CAP_USD`) with tools
   `call_read_api`, `propose_write`, `cannot_help`. Reads go through `_read()` (GET only, customer-scoped).
   Without Claude: `plan_rules()` finds a customer list operation (e.g. `/customers/{customer_id}/orders`), takes the
   latest record, and proposes a `*cancel*` operation or a body-only POST that repeats it.
3. `cannot` → route `escalate` with a note. `propose` → `assist.propose()`: reject GETs, check `MAX_WRITES`,
   `scope_to_customer`, `check_ownership`, then insert `ticket_actions` (`proposed`). `ActionBlocked` → escalate.
4. Emit `action_proposed`; ticket status `awaiting_confirmation`; `tickets.state.pending_action` holds the action.
5. If triage set `also_bug`, a `bug_reported` notification goes out too.

**Confirm turn** (`POST /api/tickets/{id}/confirm` or a typed yes/no, `graph.act_node`):
1. Declined → action `declined`, ticket `open`, nothing executed.
2. Approved → status `approved` → `assist.execute()`: `call_api()` (span `api METHOD /path`, kind `tool`), then
   `verify()` (span "verify action"). Row → `done`/`failed` with `response` and `verification`.
3. Emit `action_done`, `step verify`, `verified`. Verified → `action_taken` notification, ticket `resolved`.
   Not verified → `escalation` notification, ticket `escalated`.

A new non-yes/no message while a proposal is pending marks it `declined` (`service.post_message`).
