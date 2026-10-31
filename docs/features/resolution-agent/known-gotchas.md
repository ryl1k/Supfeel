# Known gotchas

> Status: **done** (Sprint 2). Paths below are real; keep them in sync with the code.

- Sonnet 5.5: forced `tool_choice` (`any`/`tool`) returns 400 — use structured outputs for understand/plan.
- Sonnet 5.5: `thinking: {type: "disabled"}` returns 400; control cost with `output_config.effort="low"`.
- No assistant prefill on current models — don't try to prefill JSON.
- Keep system prompts byte-stable (no timestamps/IDs) or prompt caching silently breaks.
- We do NOT use LangGraph `interrupt()`/checkpointer. Confirmation state lives in `conversations.state.pending`, and a confirm turn starts the graph at `act`. This is simpler and survives Render spin-downs and restarts.
- Verification must read fresh state from DB, not the tool's own return value.
- Clarifying-question turns must not count toward `MAX_REPLANS`.
- The whole plan is approved as one unit: if any action needs confirmation, all of them wait.
- Rule-brain helper `_a(tool, why, **args)`: don't name a parameter `reason`, since tools take a `reason` arg.
- `conversations.status` is varchar(32) (`awaiting_confirmation` is 21 chars). No migrations: change columns by hand on existing DBs.
- In mock mode the rule brain must cover every demo scenario. `tests/agent/test_scenarios.py` is the contract.
