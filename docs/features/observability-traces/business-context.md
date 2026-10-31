# Business context

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- Trace ids: ticket id (`T-XXXXXX`, all turns of a ticket), index job id (`job_<hex>`), `ask_<hex>` for repo Q&A.
- Span kinds: `run`, `step`, `llm`, `embedding`, `tool`, `retrieval`, `http`.
- Attributes are clipped (`MAX_ATTR_CHARS` 4000 per string, 50 items per list/dict) and can contain prompts,
  customer messages, API responses and tool outputs. Treat traces as sensitive.
- Cost is attached from the usage ledger, so traces cost nothing extra to compute.
