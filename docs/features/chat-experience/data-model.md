# Data model

> Status: **done** (Sprint 3). Paths below are real; keep them in sync with the code.

Client state only (no browser storage):
- `turns: Turn[]`, where a `UserTurn` is `{kind, id, text}` and an `AssistantTurn` is `{text, steps{}, proposed[], confirmation, done[], verified{}, recommendations, notices[], outcome, streaming, error}`.
- One assistant turn per request. A confirmation creates a new turn, and the proposing turn's `confirmation` becomes `approved`/`declined`.
- The conversation id is created lazily on first send. Switching persona or pressing ••• starts a new one.

Event types: see `frontend/lib/types.ts` (`AgentEvent`).
