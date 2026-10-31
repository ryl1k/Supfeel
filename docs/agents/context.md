# Agent context: current state

_Last updated: 2026-10-31, end of Sprint 5 (pivot to code-aware support)._

## Where we are

- **Product (since Sprint 5)**: import a GitHub repo → index + explain it → resolve tickets by explaining, acting
  through the business API, or fixing bugs with a PR verified by CI. Tracing, learning, notifications, push re-index.
- Backend: 64 tests passing (mock mode). Live pipeline verified with `scripts/live_support_smoke.py` ($0.18).
- Frontend: `/app` workspace, `/app/repos/[id]`, `/app/tickets[/id]`, `/app/inbox`, `/support/[repoId]`; verified
  end to end in headless Chrome against the mock backend (desktop + 390 px).
- The legacy Velora agent (`/chat`, `app/agent`, `app/tools`, `knowledge-base/`) still works and is untouched.
- Spend: $0.318 Claude, $0.0003 OpenAI (of $90 / $5).
- GitHub App `supfeel` is created and its credentials verified (app auth works). It has **no installations yet**.
  Telegram notifications are configured in the user's `.env` and delivered.

## Run locally

```bash
docker compose up -d
cd backend && uv sync && uv run python -m app.boot
ALLOW_LOCAL_REPOS=true uv run uvicorn app.main:app --reload
cd ../frontend && npm run dev                       # /app
uv run pytest                                       # DB supfeel_test
LLM_MODE=live uv run python -m scripts.live_support_smoke   # ≈ $0.2
```

`.env` points `DATABASE_URL` at **Neon**. For local runs export
`DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/supfeel` (env beats `.env`).

## Map

| Path | What |
|---|---|
| `backend/app/repos/` | `github.py` (App JWT → installation tokens, PAT, anonymous), `source.py`, `chunker.py`, `openapi.py`, `explain.py`, `indexer.py` (jobs), `search.py`, `ask.py` |
| `backend/app/support/` | `graph.py` (LangGraph), `service.py` (turn driver, follow-ups, confirm), `triage.py`, `context.py`, `assist.py` (authority), `fixer.py` (tool loop + PR), `ci.py`, `learn.py`, `notify.py` |
| `backend/app/obs/trace.py` | spans (ContextVar), `record_span`, `load_trace` |
| `backend/app/api/` | `repos.py`, `tickets.py`, `github.py` (webhook), legacy `chat.py`, `admin.py` |
| `examples/slice-pizza/` | demo target (bugs: `#`/`/` rejected in street regex; `>` instead of `>=` for free delivery) |
| `frontend/components/app/` | dashboard (Workspace, RepoView, TicketView, TraceView, Lists, ui) |
| `frontend/components/support/` | customer support chat |
| `docs/features/` | 10-file context per feature (6 new ones for Sprint 5) |

## Next up

1. Deploy (`docs/project/deployment.md`): Neon → Render (+ Secret File for the App key) → Vercel → CORS → App webhook URL.
2. Push `examples/slice-pizza` to its own **public** repo, install the App on it, import it, set its API settings.
3. Hackathon rules via DevRelay MCP after `devrelay login`.
4. Optional: retry a fix when CI fails using the failing check's log; API keys for programmatic ticket intake.

## Key decisions

- Index = one tarball per run + content-hash diff (simple, robust; "incremental" by content, not by git diff).
- Fix agent edits an in-memory overlay of indexed files; publishing re-applies `old_str → new_str` edits on the
  branch head, so a stale index can't revert newer code.
- CI on the PR is the verification for fixes; read-back is the verification for actions.
- Authority rules live in code (`assist.py`), never only in prompts.
- Every ticket turn runs in a background task (survives disconnects); trace id = ticket id.
- Learning = closed tickets embedded as `ticket` chunks in the repo index.

## Open questions

- Hackathon rules / judging criteria still unknown (DevRelay needs login).
- Render free tier sleeps; GitHub webhooks time out at 10 s → keep-alive ping; CI poller covers missed events.
