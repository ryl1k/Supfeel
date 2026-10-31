# Agent context: current state

_Last updated: 2026-10-31, end of Sprint 6 (MCP-first, workspaces, pay-as-you-go)._

## Where we are

- **Product**: Supfeel is a tier-2 support agent delivered as an **MCP server**. A business signs up, imports its
  GitHub repo (indexed + explained), and adds Supfeel to its first-line agent with a per-repo key. The agent calls
  `escalate`; Supfeel explains, acts through the business API (customer confirms), or fixes the bug with a
  CI-verified PR, and returns a relay-ready result. Tracing, learning, notifications, push re-index.
- **Billing**: pay as you go (mocked payments): credits, unit prices, monthly spend limit (resets on the 1st, UTC),
  auto-recharge, $5 welcome credit.
- **UI (late Sprint 6)**: bold white card titles, Activity items with type chip + headline + one-line root cause
  (details collapsed), tickets as a kanban board (`TicketBoard.tsx`) with search/category/channel filters.
- **Frontend**: landing (animated escalation story, flow diagram, pricing), signup/login, onboarding wizard
  (`/app/welcome`, one-click Slice demo), Board (`/app`: checklist, KPIs, charts, activity), repo page with
  Connect (MCP) tab, tickets, inbox, billing, playground (`/support/[repoId]`).
- Backend: 75 tests passing (mock mode), incl. MCP over streamable HTTP. Live Claude pipeline verified in Sprint 5.
- **LLM_MODE=live** in `.env` (switched on by the user's request). Repos indexed in mock mode must be re-indexed to
  get OpenAI embeddings (`ryl1k__supfeel` was re-indexed). Spend: $0.682 Claude, $0.0025 OpenAI (of $90 / $5).
- GitHub App `supfeel` credentials verified; **no installations yet**. Telegram notifications configured.
- `dev` is ahead of `main`; merge at sprint end.

## Run locally

```bash
docker compose up -d
cd backend && uv sync && uv run python -m app.boot
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/supfeel \
  ALLOW_LOCAL_REPOS=true OPEN_IMPORT=true uv run uvicorn app.main:app --reload
cd ../frontend && npm run dev     # http://localhost:3000 → Get started
uv run pytest                     # DB supfeel_test
```

`.env` points `DATABASE_URL` at Neon; export the local URL for local runs (env beats `.env`). If the Next dev
server throws "x is not a function" after a module's exports changed, restart it (`rm -rf .next`).

## Map

| Path | What |
|---|---|
| `backend/app/mcp_server.py` | MCP tools + key auth; mounted in `main.py` (`_mount_mcp`) |
| `backend/app/accounts/` | `auth.py` (users, sessions, keys, scoping), `billing.py` (credits), `context.py` (account ContextVar) |
| `backend/app/api/` | `accounts.py` (auth, billing, keys), `dashboard.py`, `repos.py`, `tickets.py`, `github.py` |
| `backend/app/repos/`, `backend/app/support/`, `backend/app/obs/` | indexing, ticket graph, tracing (see Sprint 5) |
| `frontend/components/app/` | Board, Welcome, RepoView, ConnectPanel, TicketView, BillingView, TraceView, Charts, Shell |
| `frontend/components/motion/` | Reveal (scroll), CountUp; motion CSS in `app/globals.css` |
| `docs/features/` | 10-file context per feature (mcp-server, accounts-billing, workspace-board are Sprint 6) |

## Next up

1. Deploy (`docs/project/deployment.md`): Neon → Render (Secret File for the App key) → Vercel → CORS → App webhook URL.
2. Push `examples/slice-pizza` to its own public repo, install the App, set `DEMO_GITHUB_REPO`.
3. Live run of the full loop on the deploy: MCP escalate from Claude Code → fix PR → CI → merge → re-index.
4. Hackathon rules via DevRelay MCP after `devrelay login`.

## Key decisions

- MCP is the main entry point; the web ticket API is the owner's playground. One key = one repository.
- Pay as you go instead of subscriptions (user's call, 2026-10-31). Charges happen when work starts; refunds when a
  fix run never reached the model. Balance checks aren't transactional (fine for the demo).
- Authority rules for actions live in code; the customer's confirmation travels through `confirm` (MCP) and must
  never be given by the calling agent on its own (tool marked destructive, documented in the server instructions).
- Categorical chart colors come from the dataviz reference palette, validated against the panel surface.
