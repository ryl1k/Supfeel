# Integration points

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

- **accounts-billing**: `resolve_key()` gives the account and repo; `open_ticket` charges `ticket`,
  `ask_product` charges `ask`, `fix_node` charges `fix`. `PaymentRequired` → `TicketError` → `ToolError`.
- **ticket-resolution**: `create_ticket` / `post_message` / `confirm` event streams; `relay()` and
  `list_tickets([repo_id])`; `handoff` in `TicketState`.
- **assisted-actions**: `pending_action` becomes `needs_confirmation`; `confirm` restarts the graph at `act`.
- **code-fix-agent**: `ci.refresh` / `ci.on_pr_closed` fire callbacks; `fix` → `engineering`.
- **repo-indexing**: `get_product_overview` reads `repos.overview`, `repo_docs` (modules), `api_operations`;
  `ask_product` uses `repos.ask.ask()`.
- **observability-traces**: turns are traced as for web tickets; `trace_url` links to the ticket page.
- MCP SDK (`mcp` 2.x, locked at 2.3.0 in `backend/uv.lock`), which brings its own HTTP client `httpx2`.
