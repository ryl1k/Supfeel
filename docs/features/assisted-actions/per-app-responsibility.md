# Per-app responsibility

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

| App | Responsibility |
|---|---|
| backend | Planning, authority rules, HTTP calls to the business API, verification, `ticket_actions` |
| business API | The real system of record (any OpenAPI-described HTTP API); Slice demo at `/demo-store` |
| Neon DB | `ticket_actions`, `tickets.state.pending_action`, `api_operations` |
| Claude | Optional planner (`assist_plan` tool loop); never decides authority |
| frontend | `ProposalCard` (approve/decline), `VerifiedCard` in the chat; `ActionsCard` on the ticket page; API settings form |
