# Integration points

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- **repo-indexing**: operations from `api_operations` (OpenAPI in the repo or `settings.api_spec_url`); credentials from `repos.settings`.
- **ticket-resolution**: `assist_node` / `act_node`, confirmation turns in `service.py`.
- **llm-budget-guard**: `tool_turn(node="assist_plan", session_cap=TICKET_CAP_USD)`.
- **business-notifications**: `action_taken`, `escalation`, `bug_reported` (`also_bug`).
- **observability-traces**: `api …` and "verify action" `tool` spans include args, status and the response (clipped).
- Demo deploy: set the repo's *Business API base URL* to `https://<service>.onrender.com/demo-store` and token `demo-service-token` (`docs/project/deployment.md`).
