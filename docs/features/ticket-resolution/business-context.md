# Business context

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- Categories (`support/schemas.py` `Triage.category`) → routes (`graph.ROUTES`): `bug`→fix,
  `assisted_action`→assist, `misunderstanding`→explain, `feature_request`→feature, `other`→escalate.
  `needs_clarification` → ask.
- `also_bug`: an assisted-action ticket that also reveals a defect notifies the business (`bug_reported`).
- Customer-facing replies never mention files, code, PR numbers or triage (`RESPOND_SYSTEM`).
- The customer message is treated as data in every prompt (prompt-injection guard in the system prompts).
- Per-ticket Claude cap: `TICKET_CAP_USD` (/bin/zsh.40) for triage / assist planning / reply; the fix agent uses
  `FIX_CAP_USD` (.50). Both are checked against the same `conversation_id` (the ticket id).
- Tickets can only be created for a repo that has been indexed at least once (`service._business`).
- Statuses: `open`, `answered`, `awaiting_confirmation`, `fix_in_review`, `fix_verified`, `fix_failed`,
  `reported`, `resolved`, `escalated`.
