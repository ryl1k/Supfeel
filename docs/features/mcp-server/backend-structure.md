# Backend structure

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

```
backend/app/mcp_server.py
  INSTRUCTIONS, mcp = MCPServer(name="Supfeel", ...)   (mcp 2.x: mcp.server.mcpserver)
  _key(ctx)            Authorization Bearer / x-api-key → auth.resolve_key → KeyContext, else ToolError
  _owned_ticket()      ticket must belong to the key's repo
  _run(ctx, events, wait)  step events → ctx.report_progress; error → ToolError; wait=False → drain in _background
  Message, Customer    pydantic tool argument models
  tools: get_product_overview, ask_product, escalate, reply, confirm, get_ticket, list_tickets
backend/app/main.py
  lifespan(): resume_tracking(), then `async with mcp.session_manager.run()` around the app
  _mount_mcp(): mcp.streamable_http_app(streamable_http_path="/mcp", stateless_http=True, host="0.0.0.0");
                its routes are appended to the FastAPI router
backend/app/support/service.py   relay(), NEXT_STEP, open_ticket(channel, meta) stores the transcript,
                                 _history() keeps customer/agent/frontline, _initial() passes meta.handoff
backend/app/support/triage.py    handoff_block() (used by triage() and graph.respond_node)
backend/app/support/state.py     TicketState.handoff
backend/app/support/callbacks.py fire(ticket_id, event): signed POST of the relay view to meta.callback_url
backend/app/support/ci.py        refresh() and on_pr_closed() call callbacks.fire
backend/app/accounts/auth.py     KeyContext, resolve_key(), create_key(), list_keys(), revoke_key()
backend/app/api/accounts.py      key routes (GET/POST /api/repos/{id}/keys, DELETE /api/keys/{id})
```
