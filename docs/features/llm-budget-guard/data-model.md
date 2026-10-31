# Data model

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

| Table | Columns |
|---|---|
| `llm_usage` | id, ts, provider (`anthropic`/`openai`), model, node, conversation_id, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, cost_usd numeric(10,6), mode |
