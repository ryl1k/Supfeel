# Agent context: current state

_Last updated: 2026-10-31, end of Sprint 0._

## Where we are

- Sprint 0 (foundation) is **done**: repo, docs, knowledge base, agent context.
- No application code exists yet.
- Active branch: `dev`. `main` holds the Sprint 0 baseline.

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
| `.env` (untracked) | Has `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` |

## Next up: Sprint 1 (backend core)

See `docs/project/roadmap.md`. Start with the central LLM client and budget guard, **before** any agent code.

## Key decisions

- Demo store: Velora (footwear/apparel). Hero scenario: uncomfortable sneakers → comfort-guarantee exchange with a wide-fit suggestion.
- Investigate and verify steps are deterministic (no LLM), so there are about 3 LLM calls per resolved issue.
- Hosting: Vercel (frontend) + Railway (backend) + Neon Postgres with pgvector (data + vectors).
- Qloo is optional, with a local fallback.

## Open questions

- Hackathon name, rules and judging criteria are unknown. Ask the user before tailoring the pitch.
- Railway trial credit ($5, 30 days) must last until the demo. Fallback is Render/HF Spaces.
