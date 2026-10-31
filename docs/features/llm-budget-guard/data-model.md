# Data model

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

| Table | Columns |
|---|---|
| `llm_usage` | id, ts, provider (`anthropic`/`openai`), model, node, conversation_id, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, cost_usd numeric(10,6), mode |
