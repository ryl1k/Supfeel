# End-to-end flow

> Status: **done** (Sprint 5, updated in Sprint 6). Paths below are real; keep them in sync with the code.

**New ticket** (`POST /api/repos/{repo_id}/tickets`, body `{customer: {name, email, ref}, message}`):
0. The route requires a signed-in owner (`CurrentPrincipal` + `repo_for`); MCP `escalate` enters at step 1 with `channel="mcp"`.
1. `service.create_ticket` → `open_ticket`: check the repo is indexed, charge `ticket` (`PaymentRequired` →
   `TicketError`), insert `tickets` (`T-XXXXXX`, channel, meta), any handoff transcript (`customer` / `frontline`)
   and the customer message, emit `ticket`.
2. `_stream` starts `_drive` in its own `asyncio` task feeding a queue (survives client disconnect). The run is
   one trace span "ticket turn (message)" with `trace_id` = ticket id.
3. Graph (`support/graph.py`, `recursion_limit=MAX_STEPS` 14):
   - **context**: `context.gather()` → top code/doc/summary hits (up to 4 queries), similar `ticket` chunks
     (score ≥ 0.35), all `api_operations`.
   - **triage**: `triage.triage()` (Claude structured output, or `rules_triage` regexes). With Claude, its
     `search_queries` trigger a second `gather`.
   - route node: `explain` (status `answered`), `assist`, `fix`, `feature` (notify, `resolved`),
     `escalate` (notify, `escalated`), `ask` (`open`). If assist can't act, it falls through to `escalate`.
   - **respond**: `stream_text` (`ticket_respond`) streams `token` events; falls back to `rules_reply`.
4. `_finish`: persist category, triage (+route, brain), fix, resolution, `state.pending_action`, status; save
   the agent reply; learn if the status is learnable (not `fix_in_review`). Emit `done`.

**Follow-up** (`POST /api/tickets/{id}/messages`):
- `awaiting_confirmation` + message matching `APPROVE` (an explicit yes / go ahead) or a short `NO` → confirm turn.
- `answered` + `SATISFIED` (yes / thanks / got it…) without a `HEDGE` word → `resolved` (learn).
  `answered` + short `NO` → `escalated` + notify.
- Otherwise a pending proposal is marked `declined` and a new message turn runs with the last 10 messages as history.

**Confirm** (`POST /api/tickets/{id}/confirm`, `{approved}`): graph starts at **act** with the pending action
restored from `tickets.state` (see `assisted-actions`). Nothing pending → `error` event `nothing_pending`.

**Failure**: any exception in a turn → `error` event (`internal`) + an `escalation` notification "Ticket … crashed".
SSE events: `ticket`, `step`, `token`, `action_proposed`, `action_done`, `verified`, `fix`, `done`, `error`.
