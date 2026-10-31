# Known gotchas

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

- Prompt cache needs a minimum prefix length; short system prompts silently won't cache — check
  `cache_read_input_tokens` in the ledger.
- Request hash for replay must exclude nothing that affects output, and include model + effort.
- `temperature`/`top_p` are rejected on current models — don't send them.
- Estimate cost *before* the call for the cap check (max_tokens × output price) to avoid overshoot.
