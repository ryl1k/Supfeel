# Agent context: current state

_Last updated: 2026-10-31, end of Sprint 1._

## Where we are

- Sprint 0 (foundation) and Sprint 1 (backend core) are **done**.
- Backend: FastAPI + Postgres/pgvector + tools + RAG + budget-guarded LLM client, with 30 tests passing.
- Not built yet: the agent graph and chat API (Sprint 2) and the frontend (Sprint 3).
- Active branch: `dev`. `main` is updated at each sprint end.

## Run locally

```bash
docker compose up -d                       # pgvector on localhost:5433
cd backend && uv sync
uv run python -m app.db.seed               # tables + demo data
uv run python -m app.rag.ingest            # embed knowledge base (mock hash in LLM_MODE=mock)
uv run uvicorn app.main:app --reload       # http://localhost:8000/api/health
uv run pytest                              # uses DB supfeel_test
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
| `docker-compose.yml` | Local pgvector Postgres (port 5433) |
| `.env` (untracked) | Has `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` |

## Next up: Sprint 2 (agent)

Build the LangGraph graph in `backend/app/agent/` per `docs/features/resolution-agent/`. Mock mode must work with no API calls (rule brain).

## Key decisions

- Demo store: Velora (footwear/apparel). Hero scenario: uncomfortable sneakers → comfort-guarantee exchange with a wide-fit suggestion.
- Investigate and verify steps are deterministic (no LLM), so there are about 3 LLM calls per resolved issue.
- Hosting: Vercel (frontend) + Railway (backend) + Neon Postgres with pgvector (data + vectors).
- Qloo is optional, with a local fallback.

## Open questions

- Hackathon name, rules and judging criteria are unknown. Ask the user before tailoring the pitch.
- Railway trial credit ($5, 30 days) must last until the demo. Fallback is Render/HF Spaces.
