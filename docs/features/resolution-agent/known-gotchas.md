# Known gotchas

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

- Sonnet 5.5: forced `tool_choice` (`any`/`tool`) returns 400 — use structured outputs for understand/plan.
- Sonnet 5.5: `thinking: {type: "disabled"}` returns 400; control cost with `output_config.effort="low"`.
- No assistant prefill on current models — don't try to prefill JSON.
- Keep system prompts byte-stable (no timestamps/IDs) or prompt caching silently breaks.
- LangGraph `interrupt()` needs a checkpointer; resume with the same `thread_id` (= conversation_id).
- Verification must read fresh state from DB, not the tool's own return value.
- Clarifying-question turns must not count toward `MAX_REPLANS`.
