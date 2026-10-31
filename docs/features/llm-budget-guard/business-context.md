# Business context

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

See `docs/project/budget.md` for all numbers. Summary:
- Model `claude-sonnet-5-5`: $2 / MTok in, $10 / MTok out, cache read $0.20 / MTok.
- App hard cap $60 Claude (`LLM_BUDGET_HARD_CAP_USD`), session cap $0.50, embeddings cap $3.
- Defaults: `LLM_MODE=mock`, `effort=low`, per-node `max_tokens` (512 / 1024 / 768).
