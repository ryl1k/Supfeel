# Backend structure

> Status: **done** (Sprint 5, updated in Sprint 6). Paths below are real; keep them in sync with the code.

```
backend/app/support/
  graph.py    nodes context / triage / explain / ask / feature / escalate / assist / act / fix / respond,
              traced() decorator (one step span per node), ROUTES, RESPOND_SYSTEM, rules_reply(), GRAPH
  service.py  open_ticket() (bills `ticket`, stores channel/meta + handoff transcript), create_ticket(), post_message(),
              confirm(), _drive() (background task + queue, sets current_account), _finish(), _close_answered(),
              APPROVE / SATISFIED / NO / HEDGE regexes, relay() + NEXT_STEP (mcp-server), get_ticket(),
              list_tickets(repo_ids), list_notifications(repo_ids), learn_ticket()
  state.py    TicketState TypedDict
  schemas.py  Triage, ActionProposal (pydantic)
  context.py  gather(), hits_block(), tickets_block(), operations_block()
  triage.py   TRIAGE_SYSTEM, rules_triage() (_BUG / _ASSIST / _FEATURE / _QUESTION regexes), triage()
  learn.py    LEARNABLE statuses, ticket_text(), learn() → kind="ticket" chunk (one per ticket, replaced)
backend/app/api/tickets.py   routes (CurrentPrincipal; ticket_for(), account_repo_ids()); _sse() maps TicketError → bad_request, others → internal
backend/app/agent/events.py  emit() / step() (shared with the legacy Velora agent)
```
