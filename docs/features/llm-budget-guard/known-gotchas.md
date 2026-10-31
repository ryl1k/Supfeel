# Known gotchas

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

- Prompt cache needs a minimum prefix length; short system prompts silently won't cache — check
  `cache_read_input_tokens` in the ledger.
- Request hash for replay must exclude nothing that affects output, and include model + effort.
- `temperature`/`top_p` are rejected on current models — don't send them.
- Estimate cost *before* the call for the cap check (max_tokens × output price) to avoid overshoot.
- Only `mode="live"` rows count toward caps; replay/cache hits cost nothing.
- `.llm-cache/` is gitignored; recordings are per-machine. Delete it to force fresh calls.
- Sonnet 5.5 rejects `thinking: {type: "disabled"}`; we send `{type: "between_tools"}` to turn thinking off for tool-less calls.
- Server-side refusal fallbacks are not enabled: they could route to a non-Sonnet model, which breaks the "Sonnet only" budget rule. Refusals fall back to the rule brain instead.
