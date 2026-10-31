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

**Notes for next sprint**
- Build the budget-guarded LLM client first. Default to `mock` mode.
- The seed data in Sprint 1 must line up with the KB policies (e.g. an order delivered 9 days ago for the hero scenario, a duplicate captured payment, a stalled shipment).
