# Known gotchas

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- Mock mode uses rule brains: `rules_triage` (keyword regexes) and `rules_reply`. The badges on the ticket page
  show which nodes used Claude vs rules (`triage.brain`).
- Per-ticket caps share one `conversation_id`: once a fix run has spent more than `TICKET_CAP_USD`, later
  turns of that ticket fall back to rules.
- `YES` also matches "thanks", "great", "perfect"…: while a proposal is pending, "thanks, but…" counts as approval.
- Every turn runs in a background task, so closing the tab doesn't stop a long fix run; the trace and DB still record it.
- The trace id is the ticket id, so one ticket trace holds every turn as a separate root span, plus CI checks.
- Chrome's `scrollIntoView` returns a Promise: effects must use braces (`useEffect(() => { el?.scrollIntoView(...) })`), or React treats the return value as a cleanup function.
- The customer `ref` comes from the client. Customer scoping trusts it; there is no customer authentication yet.
- Ticket reads (`GET /api/tickets*`) are unauthenticated, like the rest of the dashboard API.
- Learning after a normal turn runs after the turn's `run` span has closed, so its "learn from ticket" span is not
  recorded (it is recorded on PR merge, inside the "pull request closed" run).
- Legacy `app/agent/events.py` `STEPS` lists the Velora steps; ticket steps are free-form names.
