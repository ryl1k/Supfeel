# Backend structure

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

```
backend/app/llm/
  client.py         complete(), stream(); the ONLY Anthropic SDK import
  pricing.py        per-model $/MTok table (input, output, cache_write, cache_read)
  ledger.py         record(), totals(), check_caps()
  replay.py         request hashing, .llm-cache read/write
  mock_responses/   understand.json, plan.json, respond.json per demo scenario
backend/app/config.py  pydantic-settings: keys, model ids, caps, LLM_MODE
```
