# Integration points

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

- **resolution-agent** nodes call `complete()` / `stream()`.
- **knowledge-base-rag** `embeddings.py` records to the same ledger with `provider="openai"`.
- Tests set `LLM_MODE=replay` (CI) or `mock` (unit).
