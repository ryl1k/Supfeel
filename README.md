# Supfeel

**AI support that truly helps. More than answers: real solutions.**

Supfeel is customer support that has **read your code**. A business imports its GitHub repository; Supfeel
indexes and explains it. Then every customer message becomes a ticket that Supfeel resolves in one of three ways:

| The customer… | Supfeel… | Verified by |
|---|---|---|
| misunderstood how the product works | **explains** it from the product's own code and docs | the customer confirming |
| can't do something (the app is broken for them) | **acts** on their behalf through the business API, after their OK | reading the result back from the API |
| hit a real bug | **fixes** it: finds the root cause, edits the code, adds a regression test, opens a **pull request**, notifies the team | the repository's own CI |

Every step, Claude call, search, API and GitHub request is **traced** and shown as a graph. Closed tickets are
embedded back into the index, so Supfeel **learns** from previous tickets, and every push to the default branch
**re-indexes** the repository.

```
import repo → index (code-aware chunks, OpenAPI actions, module summaries) ─┐
customer message → ticket → context → triage ─┬─ explain ─────────────────┐ │
                                              ├─ assist → confirm → act → verify
                                              ├─ fix → PR → CI → merge ───┤
                                              └─ feature / escalate ──────┴→ respond → learn
```

The demo target is **Slice** (`examples/slice-pizza`), a small pizza-delivery API with an OpenAPI spec, tests, CI
and two real bugs. It is also mounted at `/demo-store` on the backend so assisted actions have a live API.

## Highlights

- **Repository knowledge**: incremental indexing (only changed files re-embedded), symbol outlines, Claude-written
  module summaries and repo overview, hybrid code search, "ask the codebase".
- **Agentic fixes**: a Claude tool-use loop (search, read, edit, create, not-a-bug) on an in-memory overlay; edits
  are re-applied on the latest branch head and pushed as a PR by the GitHub App. CI is the verification.
- **Safe actions**: only spec'd API operations; customer scoping, ownership read-back, confirmation and
  read-back verification enforced in code.
- **Transparent**: per-ticket trace graph + waterfall (tokens, cache hits, cost per call), business inbox mirrored to
  Telegram / Slack / Discord.
- **Cheap and resilient**: Claude Sonnet with prompt caching (≈ $0.04 per ticket, ≈ $0.07 to index a small repo),
  spend caps per ticket / fix / index job, and deterministic rule brains in mock mode or when the budget is hit.

## Stack

| Layer | Tech |
|---|---|
| Agents | LangGraph, Claude `claude-sonnet-5-5` (structured outputs, tool use, prompt caching) |
| Embeddings | OpenAI `text-embedding-3-small` → pgvector (HNSW) |
| Backend | Python 3.11, FastAPI, SQLAlchemy (async), SSE, GitHub App (PyJWT) |
| Frontend | Next.js 16, React 19, Tailwind v4 |
| Hosting (free) | Vercel (web), Render (API, Docker), Neon (Postgres + pgvector) |

## Run locally

```bash
cp .env.example .env               # keys optional in mock mode; GitHub App: docs/project/github-app-setup.md
docker compose up -d               # Postgres + pgvector on :5433

cd backend
uv sync
uv run python -m app.boot
ALLOW_LOCAL_REPOS=true uv run uvicorn app.main:app --reload   # http://localhost:8000/api/health

cd ../frontend
npm install
npm run dev                        # http://localhost:3000/app
```

In the workspace, import `examples/slice-pizza` as a local path (or a GitHub repo), set its API base URL to
`http://localhost:8000/demo-store` (token `demo-service-token`), then open its customer support page.

`LLM_MODE=mock` (the default) costs nothing. `LLM_MODE=live` uses Claude; spend is tracked at `/api/admin/usage`.

- Tests: `cd backend && uv run pytest` (64 tests, mock mode, DB `supfeel_test`)
- Live check of the whole pipeline: `LLM_MODE=live uv run python -m scripts.live_support_smoke` (≈ $0.2)
- Telegram setup: `uv run python -m scripts.telegram_setup`

## Repository

| Path | Purpose |
|---|---|
| `backend/app/repos/` | GitHub client, snapshots, chunking, OpenAPI discovery, summaries, indexer, search, Q&A |
| `backend/app/support/` | Ticket graph, triage, assisted actions, fix agent, CI tracking, learning, notifications |
| `backend/app/obs/` | Tracing (spans) |
| `backend/app/llm/` | Budget-guarded Claude client, pricing, usage ledger |
| `backend/app/agent/`, `app/tools/` | Legacy Velora store agent (`/chat`) |
| `frontend/` | Landing (`/`), workspace (`/app`), customer support (`/support/[repoId]`), legacy chat (`/chat`) |
| `examples/slice-pizza/` | Demo target repository |
| `docs/project/` | Brief, architecture, budget, roadmap, [deployment](docs/project/deployment.md), [GitHub App setup](docs/project/github-app-setup.md), [demo script](docs/project/demo-script.md) |
| `docs/features/` | Per-feature context (10 files each) for humans and coding agents |
| `docs/agents/` | Current state + sprint log for coding agents |

## Branches

`main` is stable and demo-ready. `dev` is for active work and is merged into `main` at the end of each sprint.
