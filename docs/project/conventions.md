# Conventions

## Git

- Branches: `main` (stable, demo-ready) and `dev` (active work). Work on `dev`; merge into `main` at sprint end.
- **One commit per task.**
- Commit message format (strict): `feat(domain): <5–6 words>`
  - Examples: `feat(repo): initialize repository structure and tooling`, `feat(agent): add verification node with readback`
  - `domain` = area touched: `repo`, `docs`, `kb`, `agents`, `backend`, `agent`, `tools`, `llm`, `rag`, `frontend`, `ui`, `deploy`, `tests`.
  - **No `Co-Authored-By` trailers or other attribution lines.**
- Never commit `.env`, API keys, `.llm-cache/` or `usage-ledger.jsonl`.

## Code

- Python: 3.11, type hints, `ruff` for lint and format, `pytest`.
- TypeScript: strict mode, ESLint + Prettier defaults from Next.js.
- Keep modules small. Each tool lives in its own function with a typed input/output schema.

## AI usage

- Claude model: `claude-sonnet-5-5`. Embeddings: `text-embedding-3-small`.
- Every LLM call goes through the central client (budget guard + ledger). Never instantiate the SDK elsewhere.
- Default `LLM_MODE=mock`. Use `live` only when the feature under work actually needs the real model.

## Docs

- Per-feature context lives in `docs/features/<feature>/` (10 files, see `docs/features/README.md`). Update it in the same commit as the code change.
- After each sprint, update `docs/agents/context.md` (current state) and `docs/agents/sprint-log.md` (what changed). Also update any `docs/project/*` file whose facts changed.
