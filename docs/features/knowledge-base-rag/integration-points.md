# Integration points

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

- **resolution-agent** `retrieve_policy` node → `retrieve()`.
- **llm-budget-guard** — embedding spend recorded in `llm_usage` with `provider="openai"`; capped by
  `EMBEDDING_BUDGET_HARD_CAP_USD`.
- **knowledge-base/** content — any edit requires re-running ingest (also run in deploy start command).
