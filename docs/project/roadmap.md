# Roadmap

Each sprint ends with: docs updated (`docs/agents/`), spend logged (`budget.md`), `dev` merged into `main`.

## Sprint 0: Foundation ✅
- Repo setup, branches (`main`, `dev`)
- Product brief, architecture, design system, budget, conventions
- Support knowledge base for the demo store (Velora)
- Agent context docs

## Sprint 1: Backend core ✅
- FastAPI skeleton, config, health endpoint
- Central LLM client with budget guard, ledger, `mock`/`replay`/`live` modes
- Mock business systems: Postgres (Neon) schema + seed fixtures (customers, orders, shipments, payments, products, subscriptions)
- Tool layer (read + write) with unit tests
- KB ingestion: chunk → embed → `kb_chunks` (pgvector); retrieval function
- Admin API: demo customers, reset, usage, KB search

## Sprint 2: Agent ✅
- LangGraph graph: understand → investigate → retrieve_policy → plan → act → verify → respond
- Confirmation step for sensitive actions (state persisted per conversation)
- SSE streaming of tokens and action events
- Scenario tests (replay) for the hero and secondary scenarios

## Sprint 3: Frontend ✅
- Landing page matching `docs/design/landing-reference.png`
- Chat page: glass chat window, action trail, confirmation cards, recommendation card
- Wire to the backend SSE stream; demo customer picker

## Sprint 4: Polish and deploy ✅ (code side)
- Deploy configs: `backend/Dockerfile`, `frontend/vercel.json`, idempotent `app.boot`; guide in `deployment.md`
- Demo reset endpoint + button, 6 seeded demo personas
- GitHub Actions CI (backend tests on pgvector, frontend lint + build)
- README, demo script

## Open / next
- **Actual deploy**: needs the user's Neon, Render and Vercel accounts (follow `deployment.md`)
- Fetch the hackathon rules and judging criteria via the DevRelay MCP and tailor the pitch
- Optional: Qloo integration (the recommendation provider hook exists), restoring the transcript on page reload

## Sprint 5: Code-aware support (pivot) ✅

- GitHub App client, repository import + incremental indexing (code-aware chunks, OpenAPI actions, module
  summaries, overview), Q&A over the repo
- Ticket graph: triage → explain / assisted action / fix PR / feature / escalate, learning from closed tickets
- Fix agent (Claude tool loop) → PR → CI verification → merge closes the ticket; push webhook re-indexes
- Tracing for every step and call with a graph UI; Telegram / Slack / Discord notifications
- Workspace dashboard, ticket pages, customer support page; Slice demo target repo

## Next

- Deploy (Render + Neon + Vercel), push Slice to its own public repo, install the App, set the webhook URL
- Optional: auto-retry a fix when CI fails (feed the failing check log back to the agent)
- Optional: per-repo API keys for programmatic ticket intake (widget embed)
