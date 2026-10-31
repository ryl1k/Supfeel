# Backend structure

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

```
backend/app/llm/
  client.py   complete_json(), stream_text(), strict_schema(); the ONLY anthropic import
  pricing.py  PRICES ($/MTok) + cost_usd(); unknown models priced pessimistically
  ledger.py   record(), total_spend(), check_caps() → BudgetExceeded, summary()
backend/app/config.py  Settings (pydantic-settings, reads repo .env): keys, models, caps, LLM_MODE
```
No canned mock responses: mock mode is the agent's deterministic rule brain (see resolution-agent).
