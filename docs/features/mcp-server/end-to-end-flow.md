# End-to-end flow

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

**Connect**: owner creates a key (`POST /api/repos/{id}/keys`) in `ConnectPanel`, copies a snippet
(`claude mcp add --transport http supfeel <API>/mcp --header "Authorization: Bearer sf_live_…"`).

**Every tool call** (`mcp_server.py`):
1. `_key(ctx)` reads `Authorization: Bearer …` (or `x-api-key`) from `ctx.headers` → `auth.resolve_key()`
   (sha256 lookup, not revoked, updates `last_used_at`) → `KeyContext(key_id, key_name, account_id, repo_id)`.
   Missing / bad key → `ToolError`.
2. Ticket tools check ownership with `_owned_ticket()` (ticket's `repo_id` must equal the key's) → else
   `ToolError("Unknown ticket …")`.

**escalate** (`message`, `customer`, `conversation`, `attempted`, `agent`, `callback_url`, `wait=true`):
1. Build `meta = {handoff: {agent, attempted, transcript[-20:]}, key_id, callback_url?}`.
2. `service.create_ticket(..., channel="mcp", meta=meta)` → `open_ticket` charges `ticket` (raises
   `TicketError` on `PaymentRequired`), stores transcript messages (`customer`/`user` → `customer`, others →
   `frontline`), then the customer's message. The turn runs in `_drive` like a web ticket, with `handoff` in state.
3. `_run(ctx, events, wait)`: with `wait`, consumes events, forwards each `step` with a detail as
   `ctx.report_progress(n, None, "step: detail")` (best effort), turns an `error` event or `TicketError` into a
   `ToolError`. With `wait=false`, reads only the first (`ticket`) event, drains the rest in a background task
   kept in `_background`, and returns immediately.
4. Returns `service.relay(ticket_id)`: `ticket_id`, `status`, `category`, `customer_reply` (last agent message),
   `next_step` (`NEXT_STEP[status]`), `trace_url` (`PUBLIC_APP_URL/app/tickets/{id}`), plus
   `needs_confirmation {question, action, details}` when an action is pending and `engineering {decision,
   root_cause, pr_url, workaround, ci}` when there is a fix.

**reply** → `service.post_message` (yes/no logic as on the web) → relay. **confirm** → checks
`awaiting_confirmation`, `service.confirm` → relay. **get_ticket** → relay. **list_tickets** → last 25 for
the key's repo. **get_product_overview** → business name, status, overview, module keys, non-GET actions,
prices. **ask_product** → charge `ask`, `repos.ask.ask()` → `{answer, citations, confidence}`.

**Later changes**: `ci.refresh()` (status change, e.g. `fix_verified` / `fix_failed`) and `ci.on_pr_closed()`
(merged → `resolved`) call `callbacks.fire(ticket_id, event)`: POST `{event, ticket: relay}` to
`meta.callback_url` with `X-Supfeel-Event` and `X-Supfeel-Signature: sha256=<HMAC(key_id, body)>`, 10 s timeout,
traced as an `http` span "callback <event>". Failures are logged, never retried.
