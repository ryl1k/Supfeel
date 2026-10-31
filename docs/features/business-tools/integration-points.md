# Integration points

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

- **resolution-agent** calls `registry.call`; tool defs exported for Claude via `to_claude_tool_defs()`.
- **chat-experience** renders `action_*` events produced from `action_log`.
- **Qloo** (optional, `QLOO_API_KEY`): `get_recommendations`; must degrade gracefully.
- Seed data ↔ `knowledge-base/` numbers (windows, thresholds) must stay consistent.
