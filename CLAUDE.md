# Supfeel: agent instructions

Hackathon project: an AI customer-support agent that understands, investigates, acts and **verifies**. Read these before starting work:

1. `docs/agents/context.md`: current state, what's next, open questions (**read first**)
2. `docs/project/conventions.md`: git and commit rules, code style
3. `docs/project/budget.md`: API spend limits and mandatory cost controls
4. `docs/project/architecture.md` and `docs/project/design-system.md`, as relevant to the task

## Non-negotiables

- **Commits**: one per task, format `feat(domain): <5–6 words>`, **no Co-Authored-By or any attribution trailer**.
- **Branch**: work on `dev`. `main` only receives sprint merges.
- **Budget**: $90 Claude / $5 OpenAI in total. Model `claude-sonnet-5-5`, embeddings `text-embedding-3-small`. All LLM calls go through the central budget-guarded client. Default `LLM_MODE=mock`.
- **Deploys**: free tiers only (Vercel, Render or HF Spaces).
- **UI**: must match `docs/design/landing-reference.png` and `docs/project/design-system.md`.
- **Never commit** `.env` or keys.
- **End of sprint**: update `docs/agents/context.md`, append to `docs/agents/sprint-log.md`, log spend in `docs/project/budget.md`, and merge `dev` → `main`.
