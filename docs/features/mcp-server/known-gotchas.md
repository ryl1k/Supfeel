# Known gotchas

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

- **The session manager can run only once per process.** `mcp.session_manager.run()` lives in the app
  `lifespan`; in tests the module fixture `mcp_running` runs it in its own task, because it owns an anyio
  task group that must enter and exit in the same task.
- **`host="0.0.0.0"` in `_mount_mcp` is deliberate.** With the default `127.0.0.1` the SDK enables
  DNS-rebinding protection that only allows localhost `Host` headers, which rejects every request behind
  Render. The per-repository keys are the access control.
- The SDK uses **`httpx2`**, not `httpx`: test clients and the Python snippet must use
  `httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app))`. FastAPI tests elsewhere still use `httpx`.
- Stateless HTTP: no MCP session survives between calls, so all continuity is the `ticket_id`.
- `wait=false` drains the turn in an in-process task (`_background`): a restart loses the rest of the turn.
  The agent must poll `get_ticket`.
- Progress notifications are best effort. Clients that didn't send a progress token get none; failures are swallowed.
- `ToolError` messages reach the agent as `is_error` results prefixed `Error executing tool <name>: `. Any other
  exception becomes the SDK's `UnexpectedToolError` with no message. With `wait=false`, a `TicketError` raised
  before the first event (e.g. out of credit in `open_ticket`) is not converted in `_run`, so the agent gets
  only the generic error.
- Callbacks are best effort (no retry), and the signature key is the key's **id**, not a secret: it is an
  integrity check for the demo, not authentication.
- `pyproject.toml` says `mcp>=1.20`, but the code needs the 2.x `mcp.server.mcpserver` API (lock pins 2.3.0).
