# Supfeel: agent instructions

Hackathon project: code-aware AI customer support. A business imports its GitHub repo; Supfeel indexes it and
resolves tickets by explaining, acting through the business API, or fixing bugs with a CI-verified PR. Read these before starting work:

1. `docs/agents/context.md`: current state, what's next, open questions (**read first**)
2. `docs/project/conventions.md`: git and commit rules, code style
3. `docs/project/budget.md`: API spend limits and mandatory cost controls
4. `docs/features/<feature>/`: 10-file business + code context for the feature you are touching (index: `docs/features/README.md`)
5. `docs/project/architecture.md` and `docs/project/design-system.md`, as relevant to the task

## Non-negotiables

- **Commits**: one per task, format `feat(domain): <5–6 words>`, **no Co-Authored-By or any attribution trailer**.
- **Branch**: work on `dev`. `main` only receives sprint merges.
- **Budget**: $90 Claude / $5 OpenAI in total. Model `claude-sonnet-5-5`, embeddings `text-embedding-3-small`. All LLM calls go through the central budget-guarded client. Default `LLM_MODE=mock`.
- **Deploys**: free tiers only: Vercel (frontend), Render (backend, Docker), Neon Postgres + pgvector (DB).
- **UI**: must match `docs/design/landing-reference.png` and `docs/project/design-system.md`.
- **Never commit** `.env` or keys (`*.pem` is gitignored; the GitHub App key lives in `~/.secrets/`).
- **Tracing**: new steps / external calls go inside `app.obs.trace.span(...)`.
- **Feature docs**: when you change a feature, update its `docs/features/<feature>/` files in the same task. New feature → copy `docs/features/_template/`.
- **End of sprint**: update `docs/agents/context.md`, append to `docs/agents/sprint-log.md`, log spend in `docs/project/budget.md`, and merge `dev` → `main`.
