# Integration points

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

- **resolution-agent** calls `registry.call`; tool defs exported for Claude via `to_claude_tool_defs()`.
- **chat-experience** renders `action_*` events produced from `action_log`.
- **Qloo** (optional, `QLOO_API_KEY`): `get_recommendations`; must degrade gracefully.
- Seed data ↔ `knowledge-base/` numbers (windows, thresholds) must stay consistent.
