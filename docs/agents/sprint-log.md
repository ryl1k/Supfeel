# Sprint log

Append one entry per sprint (newest at the bottom).

## Sprint 0: Foundation (2026-10-31)

**Done**
- Repo initialized (`.gitignore`, `.env.example`, `.editorconfig`, README), remote `origin`, branches `main` + `dev`
- Project docs: brief, architecture, design system, budget, roadmap, conventions
- Velora knowledge base: returns/exchanges, refunds, shipping, payments, membership, warranty, account/privacy, agent authority (internal), sizing, care, general
- Agent context: `CLAUDE.md`, `docs/agents/`
- Per-feature context `docs/features/` (10-file structure) for resolution-agent, business-tools, knowledge-base-rag, llm-budget-guard, chat-experience, landing-page
- Hosting decided: Vercel + Railway + Neon (pgvector replaces the in-process `.npz` plan)

**Spend**: Claude $0.00, OpenAI $0.00


## Sprint 1: Backend core (2026-10-31)

**Done**
- `backend/` (uv, Python 3.11): FastAPI app, settings that read the repo `.env`, async SQLAlchemy + asyncpg
- Local DB: `docker-compose.yml` with `pgvector/pgvector:pg16` on port **5433** (dev DB `supfeel`, test DB `supfeel_test`)
- Schema (17 tables) + deterministic seed with 6 demo personas that match the KB policies
- Budget-guarded Claude client (`app/llm/`): caps, `llm_usage` ledger, request-hash recordings, mock/replay/live
- 18 tools (8 read, 10 write) with invariants, customer scoping, idempotent execution, read-back verification
- RAG: chunk on `##` → embeddings (mock hash or OpenAI) → pgvector HNSW; `retrieve()` + `get_section()`
- Admin API: `/api/customers/demo`, `/api/admin/reset`, `/api/demo/reset`, `/api/admin/usage`, `/api/admin/kb/search`
- 30 backend tests (`uv run pytest`)

**Spend**: Claude $0.00, OpenAI $0.00

**Decisions / changes vs plan**
- Products split into `products` + `variants` (size/width SKUs)
- Mock mode = deterministic rule brain (Sprint 2) instead of canned JSON responses
- Recordings in `.llm-cache/` are also reused as a cache in live mode
- Recommendations: local taste ranking ("velora-taste"). Qloo is not wired yet, so the UI must not claim "powered by Qloo"

**Next**: Sprint 2: LangGraph agent + SSE chat API.
