# End-to-end flow

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

`complete(node, system, messages, schema=None)`:
1. Mode `mock` → return canned response for `node` from `app/llm/mock_responses/`. Done.
2. Compute request hash. Mode `replay` → load `.llm-cache/<hash>.json` or raise `ReplayMiss`.
3. Mode `live` → check caps (sum of `llm_usage` + estimated cost). Over cap → raise `BudgetExceeded`.
4. Call Claude with `cache_control` after the frozen system/tools prefix, `output_config.effort`.
5. Record `usage` → USD via `pricing.py` → insert `llm_usage`. Save response to `.llm-cache/`.
