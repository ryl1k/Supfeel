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

## Sprint 2: Agent (2026-10-31)

**Done**
- LangGraph resolution agent (`backend/app/agent/`): understand → investigate → policy → plan → act → verify → respond
- Two brains: Claude (structured outputs, cached system prompt) and a deterministic rule brain (mock mode + automatic fallback on API error / refusal / budget cap)
- Code-enforced authority: confirmations, $200 escalation limit, arg validation
- Confirmation flow persisted in `conversations.state`; typed "yes"/"no" also works
- Verification failures automatically hand off to a human (`escalate_to_human`)
- SSE API: `POST /api/chat`, `POST /api/chat/confirm`, `GET /api/conversations/{id}`
- 10 scenario tests covering all 6 personas + decline, human, policy Q&A, error; 41 backend tests total
- `scripts/live_smoke.py`: verified the real Claude path end to end

**Spend**: Claude $0.068, OpenAI $0.0001 (cumulative $0.07 of $90)

**Tooling**: DevRelay MCP (MLH + DEV) installed for Claude Code at the user's request. It needs `devrelay login` + a restart. Use it to find the event's rules, judging criteria and sponsor tracks.

**Next**: Sprint 3: Next.js frontend (landing + chat).

## Sprint 3: Frontend (2026-10-31)

**Done**
- `frontend/`: Next.js 16.4 (App Router, `cacheComponents`), Tailwind v4, Figtree
- Landing `/` matching the reference mock (nav, 3-line hero, glass chat preview, waves, round-brilliant gem), plus Features / How it works / About sections
- Chat `/chat`: persona picker, suggested prompts, streaming replies, step trail with policy citations, confirmation card, verified action cards, recommendations, demo reset
- Verified end to end in headless Chrome against the mock backend (hero: ask → propose → approve → 2 verified actions)
- Rule-brain and LLM reply style shortened when a confirmation card is shown (no duplicated details)

**Spend**: $0 (mock mode)

**Next**: Sprint 4: deployment configs (Vercel + Railway + Neon), README, demo script.

## Sprint 4: Deploy prep + polish (2026-10-31)

**Done**
- `backend/Dockerfile` (uv, slim; ~145 MB RAM at runtime), `.dockerignore`, `railway.json` (healthcheck `/api/health`)
- `app.boot`: creates the schema + pgvector extension, seeds only an empty DB, ingests the KB idempotently
- Neon URL normalization for asyncpg (`sslmode`/`channel_binding` stripped, SSL on), `CORS_ORIGIN_REGEX` for Vercel previews
- `frontend/vercel.json`; `docs/project/deployment.md` step by step; verified the container locally against a fresh DB
- GitHub Actions CI; rule-brain routing fixes (membership cancel, address change, switching to a refund mid-proposal); 51 tests
- `docs/project/demo-script.md`, final README

**Spend**: Claude $0.067 (second live smoke run). Cumulative $0.135 / $90, OpenAI $0.0001 / $5

**Not done (needs the user)**: the real deploy (accounts/logins for Neon, Railway, Vercel), a `devrelay login` to fetch the hackathon rules.

## Sprint 5: Pivot to code-aware support (2026-10-31)

**Done**
- GitHub App integration (installation tokens, PAT fallback, anonymous public reads), webhook with HMAC check
- Repository indexing: tarball snapshots, filters/limits, code-aware chunking + outlines, OpenAPI → API operations,
  Claude module summaries + overview (hash-skipped when unchanged), hybrid search, "ask the codebase"
- Ticket graph: context → triage → explain / assist / fix / feature / escalate → respond; follow-ups, typed yes/no
- Assisted actions with code-enforced authority + read-back verification; fix agent (Claude tool loop) → PR → CI
  poller/webhooks → merge resolves the ticket; learning from closed tickets; push re-index
- Tracing (`spans`) for runs, steps, LLM, embeddings, search, tools, HTTP; trace graph + waterfall UI
- Notifications: inbox + Telegram / Slack / Discord (`scripts/telegram_setup.py`)
- Frontend workspace, repo, ticket, inbox and customer support pages; landing copy updated
- Slice demo target repo (`examples/slice-pizza`), mounted at `/demo-store`
- 64 backend tests; live smoke `scripts/live_support_smoke.py`

**Spend**: Claude $0.183, OpenAI $0.0002 (one live smoke). Cumulative $0.318 / $90, OpenAI $0.0003 / $5

**Fixed along the way**: `.pem` key was in the repo root unignored (moved to `~/.secrets`, `*.pem` ignored); empty
duplicate `DATABASE_URL` in `.env` removed; Chrome's `scrollIntoView` returning a Promise broke an effect.

**Next**: deploy, publish Slice as its own repo, install the App, run the PR → CI → merge loop live.

## Sprint 6: MCP-first, workspaces, pay as you go (2026-10-31)

**Done**
- MCP server at `/mcp` (MCP Python SDK 2.x, stateless streamable HTTP): escalate (with handoff transcript,
  progress notifications, wait/background), reply, confirm (destructive), get_ticket, list_tickets, ask_product,
  get_product_overview; relay-ready results; callbacks on later changes
- Workspaces: email + password (scrypt), sessions, per-repo API keys (hashed), account scoping on every endpoint
- Pay-as-you-go billing (mocked): credit ledger, unit prices, monthly limit, auto-recharge, top-ups, statement;
  AI spend attributed per account
- Review fixes from the docs pass: strict approval regex, cross-customer lookups blocked, protected CI paths,
  no overwriting un-indexed files, CI-less repos settle, model-switch rebuild keeps summaries + learned tickets
- Board (`/api/dashboard`), onboarding wizard with one-click demo, Connect tab, Billing page, login/signup
- Motion system: landing escalation story, animated flow diagram, scroll reveals, skeletons, count-ups, page transitions
- 75 backend tests; browser walkthrough of signup → onboarding → playground ticket → board → billing

**Spend**: $0 (all mock mode). Cumulative $0.318 / $90 Claude, $0.0003 / $5 OpenAI

**Next**: deploy; publish Slice; live MCP → PR → CI → merge loop on the deploy.
