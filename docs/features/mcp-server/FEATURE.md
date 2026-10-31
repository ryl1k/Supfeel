# MCP server

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

Supfeel's main entry point for agents. A business adds Supfeel's MCP server (streamable HTTP at `/mcp`) to its
own first-line support agent (Claude Code, Cursor, Claude Desktop, or its own bot on the MCP SDK). When that
agent can't solve a customer's problem it calls `escalate` with the conversation so far; Supfeel explains,
acts through the business API (after the customer confirms) or fixes the bug with a CI-verified PR, and
returns a **relay-ready** result: `customer_reply` to send as-is plus `next_step`.

## Why
Businesses already have a first-line bot. Supfeel is tier 2 behind it: the bot keeps the conversation, Supfeel
brings the code-level understanding, actions and verification. MCP makes that a one-line integration.

## Scope
- In: `MCPServer` and its 7 tools, per-repository key auth, progress forwarding, background (`wait=false`)
  mode, relay view (`service.relay`, `NEXT_STEP`), handoff context (transcript, attempted, agent name),
  callbacks on later ticket changes, mounting in FastAPI, the Connect tab (keys + client snippets).
- Out: key storage and billing (`accounts-billing`), the ticket graph (`ticket-resolution`), actions
  (`assisted-actions`), fixes and CI (`code-fix-agent`).

## Success criteria
- `backend/tests/support/test_mcp.py` passes in `LLM_MODE=mock`: tools listed, bad key → tool error, escalate →
  `answered` → `resolved`, action needs `confirm`, out of credit → clear tool error, other products' tickets invisible.
- An agent never has to confirm a write on the customer's behalf: `needs_confirmation` carries the question.
- Works behind Render's proxy and across restarts (stateless HTTP, no server-side MCP session).
