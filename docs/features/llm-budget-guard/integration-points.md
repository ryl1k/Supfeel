# Integration points

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

- **resolution-agent** nodes call `complete()` / `stream()`.
- **knowledge-base-rag** `embeddings.py` records to the same ledger with `provider="openai"`.
- Tests set `LLM_MODE=replay` (CI) or `mock` (unit).
