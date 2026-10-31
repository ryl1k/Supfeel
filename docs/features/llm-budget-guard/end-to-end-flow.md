# End-to-end flow

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

`complete_json(node, system, user, schema, max_tokens, conversation_id, effort=None)` and
`stream_text(node, system, user, max_tokens, conversation_id)`:

1. `LLM_MODE=mock` → raise `LlmUnavailable`. The agent catches this and uses its rule-based brain (no API).
2. Build params: frozen `system` block with `cache_control`, single user turn, `thinking: between_tools`
   (= off) unless `effort` is given (then adaptive + that effort). JSON nodes add
   `output_config.format = json_schema(strict_schema(Model))`.
3. Hash params → `.llm-cache/<sha256>.json`. **Hit → return it in any mode** (free re-runs).
4. Miss + `replay` → raise `ReplayMiss`.
5. Miss + `live` → `check_caps()` with a pessimistic estimate → call → `record()` usage to `llm_usage` →
   check `stop_reason` (refusal / max_tokens → `LlmUnavailable`) → save recording.
