# Supfeel

**AI support that truly helps. More than answers: real solutions.**

Supfeel is an AI customer-support agent that takes responsibility for the outcome. It **understands** the
customer's real problem, **investigates** their account, **plans** within written company policy, **acts**
through business tools (exchanges, refunds, reships, cancellations, address changes…) and **verifies** the
fix by re-reading system state, all visible to the customer as it happens.

```
understand → investigate → policy (RAG) → plan → [customer approval] → act → verify → respond
```

The demo runs against **Velora**, a fictional footwear store with mock orders, shipments, payments and memberships.

## Highlights

- **Agentic, not chatty**: tool calls change real (mock) state in Postgres.
- **Verification loop**: every write is checked by reading the database again. Failures go to a human automatically.
- **Policy-grounded**: decisions cite the knowledge base (`knowledge-base/`, pgvector RAG).
- **Safe by design**: confirmation and escalation rules (sensitive actions, refunds > $200) are enforced in code, not in the prompt.
- **Resilient and cheap**: Claude Sonnet with prompt caching (≈ $0.02 per resolved issue). Investigation and verification are deterministic. A rule-based brain takes over automatically in mock mode, on API errors, or when the budget cap is hit.
- **Transparent UI**: live step trail with policy citations, approval cards, and verified action receipts.

## Stack

| Layer | Tech |
|---|---|
| Agent | LangGraph, Claude `claude-sonnet-5-5` (structured outputs, prompt caching) |
| Embeddings | OpenAI `text-embedding-3-small` → pgvector (HNSW) |
| Backend | Python 3.11, FastAPI, SQLAlchemy (async), SSE |
| Frontend | Next.js 16, React 19, Tailwind v4 |
| Hosting (free) | Vercel (web), Render (API, Docker), Neon (Postgres + pgvector) |

## Run locally

```bash
cp .env.example .env               # add ANTHROPIC_API_KEY / OPENAI_API_KEY (optional in mock mode)
docker compose up -d               # Postgres + pgvector on :5433

cd backend
uv sync
uv run python -m app.boot          # tables + demo data + knowledge base
uv run uvicorn app.main:app --reload   # http://localhost:8000/api/health

cd ../frontend
npm install
npm run dev                        # http://localhost:3000
```

`LLM_MODE=mock` (the default) costs nothing: the agent runs on its deterministic rule brain.
Set `LLM_MODE=live` to use Claude. Spend is capped (`LLM_BUDGET_HARD_CAP_USD`) and tracked at `/api/admin/usage`.

Tests: `cd backend && uv run pytest` (51 tests, mock mode, uses DB `supfeel_test`).
Live end-to-end check: `LLM_MODE=live uv run python -m scripts.live_smoke` (≈ $0.07 on a cold cache).

## Repository

| Path | Purpose |
|---|---|
| `backend/app/agent/` | LangGraph graph, brains (Claude + rules), authority rules, conversation service |
| `backend/app/tools/` | Mock Velora business systems: read/write tools + verifiers |
| `backend/app/rag/` | Knowledge-base ingestion and retrieval |
| `backend/app/llm/` | Budget-guarded Claude client, pricing, usage ledger |
| `frontend/` | Landing page (`/`) and chat (`/chat`) |
| `knowledge-base/` | Velora policies + FAQ (RAG source) |
| `docs/project/` | Brief, architecture, design system, budget, roadmap, [deployment](docs/project/deployment.md), [demo script](docs/project/demo-script.md) |
| `docs/features/` | Per-feature context (10 files each) for humans and coding agents |
| `docs/agents/` | Current state + sprint log for coding agents |

## Branches

`main` is stable and demo-ready. `dev` is for active work and is merged into `main` at the end of each sprint.
