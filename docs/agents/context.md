# Agent context: current state

_Last updated: 2026-10-31, end of Sprint 3._

## Where we are

- Sprints 0–3 are **done**: backend (agent + SSE API, 41 tests) and frontend (landing + chat) both work locally.
- Live Claude path verified (≈ $0.017 per turn). Total spend so far: $0.07.
- Remaining: deployment (Sprint 4).
- Active branch: `dev`. `main` is updated at each sprint end.

## Run locally

```bash
docker compose up -d                       # pgvector on localhost:5433
cd backend && uv sync
uv run python -m app.db.seed               # tables + demo data
uv run python -m app.rag.ingest            # embed knowledge base (mock hash in LLM_MODE=mock)
uv run uvicorn app.main:app --reload       # http://localhost:8000/api/health
cd ../frontend && npm install && npm run dev  # http://localhost:3000 (NEXT_PUBLIC_API_URL defaults to :8000)
uv run pytest                              # uses DB supfeel_test
LLM_MODE=live uv run python -m scripts.live_smoke   # real Claude end to end (~$0.07, then cached)
```

## What exists

| Path | What |
|---|---|
| `docs/project/brief.md` | Product, demo narrative, scenarios |
| `docs/project/architecture.md` | Proposed stack and LangGraph design (FastAPI + Next.js) |
| `docs/project/design-system.md` | Color/typography tokens and components from the landing mock |
| `docs/project/budget.md` | Spend targets, per-call estimates, mandatory cost controls |
| `docs/project/roadmap.md` | Sprints 0–4 |
| `docs/project/conventions.md` | Git/commit/code rules |
| `docs/features/` | Per-feature context (10 files each) for 6 planned features + `_template` |
| `knowledge-base/` | 8 policy docs + 3 FAQ docs for the fictional store **Velora** |
| `backend/` | FastAPI app: `app/db`, `app/llm`, `app/tools`, `app/rag`, `app/api` |
| `frontend/` | Next.js 16 app: `/` landing, `/chat` agent UI |
| `docker-compose.yml` | Local pgvector Postgres (port 5433) |
| `.env` (untracked) | Has `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` |

## Next up: Sprint 4 (deploy)

Dockerfile + Railway config for the backend, Vercel for the frontend, a Neon `DATABASE_URL`. Accounts are needed from the user.

## Key decisions

- Demo store: Velora (footwear/apparel). Hero scenario: uncomfortable sneakers → comfort-guarantee exchange with a wide-fit suggestion.
- Investigate and verify steps are deterministic (no LLM), so there are about 3 LLM calls per resolved issue.
- Hosting: Vercel (frontend) + Railway (backend) + Neon Postgres with pgvector (data + vectors).
- Qloo is optional, with a local fallback.

## Open questions

- Hackathon name, rules and judging criteria are unknown. The event is MLH-affiliated, so once the user runs `devrelay login`, use the DevRelay MCP (`get_mlh_event`) to fetch them.
- Railway trial credit ($5, 30 days) must last until the demo. Fallback is Render/HF Spaces.
