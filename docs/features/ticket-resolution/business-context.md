# Business context

> Status: **done** (Sprint 5, updated in Sprint 6). Paths below are real; keep them in sync with the code.

- Categories (`support/schemas.py` `Triage.category`) → routes (`graph.ROUTES`): `bug`→fix,
  `assisted_action`→assist, `misunderstanding`→explain, `feature_request`→feature, `other`→escalate.
  `needs_clarification` → ask.
- `also_bug`: an assisted-action ticket that also reveals a defect notifies the business (`bug_reported`).
- Customer-facing replies never mention files, code, PR numbers or triage (`RESPOND_SYSTEM`).
- The customer message is treated as data in every prompt (prompt-injection guard in the system prompts).
- Per-ticket Claude cap: `TICKET_CAP_USD` for triage / assist planning / reply (`conversation_id` = ticket id);
  the fix agent uses `FIX_CAP_USD` against its own `conversation_id` `{ticket}:fix`.
- Tickets can only be created for a repo that has been indexed at least once (`service._business`).
- Each new ticket is billed $0.15 (`ticket`) in `open_ticket`, before the turn starts; no credit / monthly limit
  reached → `TicketError` (see `accounts-billing`).
- Channels: `web` (the signed-in owner's playground at `/support/{repoId}`) and `mcp` (escalations from a
  first-line agent, see `mcp-server`). The web endpoints require a signed-in workspace that owns the repo.
- Statuses: `open`, `answered`, `awaiting_confirmation`, `fix_in_review`, `fix_verified`, `fix_failed`,
  `reported`, `resolved`, `escalated`.
