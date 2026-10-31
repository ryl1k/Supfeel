# Frontend structure

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

- `frontend/components/app/ConnectPanel.tsx` (repo page tab `connect`, `/app/repos/{id}?tab=connect`):
  endpoint `${API_URL}/mcp`, key form (`api.createKey`), one-time key display, active keys with last use and
  Revoke (`api.keys`, `api.revokeKey`, polled every 30 s), `snippet()` per client: Claude Code
  (`claude mcp add --transport http`), Cursor (`mcpServers.url + headers`), Claude Desktop (`npx -y mcp-remote
  <url> --header Authorization:Bearer …`), Python SDK (`httpx2` + `mcp.Client` + `streamable_http_client`).
  `TOOLS` lists each tool with its price.
- `frontend/components/app/RepoView.tsx`: the `Connect (MCP)` tab; `?tab=` selects the initial tab.
- `frontend/components/app/Welcome.tsx` step "Add Supfeel to your agent": creates a key and shows the Claude Code command.
- Types / client: `ApiKey`, `api.keys`, `api.createKey`, `api.revokeKey` in `frontend/lib/workspace.ts`.
