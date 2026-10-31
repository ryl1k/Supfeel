# Agent context: current state

_Last updated: 2026-10-31, end of Sprint 4._

## Where we are

- Sprints 0–4 are **done** on the code side: backend (agent + SSE API, 51 tests), frontend (landing + chat), deploy configs, CI.
- Live Claude path verified twice (≈ $0.017 per turn). Total spend: $0.135 Claude, $0.0001 OpenAI.
- Remaining: the real deploy, which needs the user's accounts (`docs/project/deployment.md`), and the hackathon rules (DevRelay MCP).
- Active branch: `dev`. `main` is updated at each sprint end.

## Run locally

```bash
docker compose up -d                       # pgvector on localhost:5433
cd backend && uv sync
uv run python -m app.boot                  # tables + demo data (if empty) + KB embeddings
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
| `backend/Dockerfile`, `railway.json`, `frontend/vercel.json` | Deploy configs (see `docs/project/deployment.md`) |
| `.github/workflows/ci.yml` | CI: backend tests + frontend build |
| `docker-compose.yml` | Local pgvector Postgres (port 5433) |
| `.env` (untracked) | Has `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` |

## Next up

1. Deploy per `docs/project/deployment.md` (Neon → Railway → Vercel → CORS).
2. After the user runs `devrelay login` and restarts Claude Code: fetch the event's rules, judging criteria and sponsor tracks (DevRelay MCP), then tailor `docs/project/brief.md` and the demo script.
3. Nice-to-have: restore the transcript on reload, Qloo provider.

## Key decisions

- Demo store: Velora (footwear/apparel). Hero scenario: uncomfortable sneakers → comfort-guarantee exchange with a wide-fit suggestion.
- Investigate and verify steps are deterministic (no LLM), so there are about 3 LLM calls per resolved issue.
- Hosting: Vercel (frontend) + Railway (backend) + Neon Postgres with pgvector (data + vectors).
- Qloo is optional, with a local fallback.

## Open questions

- Hackathon name, rules and judging criteria are unknown. The event is MLH-affiliated, so once the user runs `devrelay login`, use the DevRelay MCP (`get_mlh_event`) to fetch them.
- Railway trial credit ($5, 30 days) must last until the demo. Fallback is Render/HF Spaces.
