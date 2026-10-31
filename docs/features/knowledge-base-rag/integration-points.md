# Integration points

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

- **resolution-agent** `retrieve_policy` node → `retrieve()`.
- **llm-budget-guard** — embedding spend recorded in `llm_usage` with `provider="openai"`; capped by
  `EMBEDDING_BUDGET_HARD_CAP_USD`.
- **knowledge-base/** content — any edit requires re-running ingest (also run in deploy start command).
