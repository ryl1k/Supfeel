# Known gotchas

> Status: **done** (Sprint 5, updated in Sprint 6). Paths below are real; keep them in sync with the code.

- Mock mode uses rule brains: `rules_triage` (keyword regexes) and `rules_reply`. The badges on the ticket page
  show which nodes used Claude vs rules (`triage.brain`).
- The fix agent spends under its own `conversation_id` (`{ticket}:fix`), so a long fix run no longer pushes later
  turns of the ticket past `TICKET_CAP_USD`.
- Approval is strict (`APPROVE` is anchored: "yes", "go ahead", "sounds good"…, nothing after but "please"), while
  closing an answered ticket is loose (`SATISFIED` prefix, unless a `HEDGE` word like "but" / "actually" appears).
- Every turn runs in a background task, so closing the tab doesn't stop a long fix run; the trace and DB still record it.
- The trace id is the ticket id, so one ticket trace holds every turn as a separate root span, plus CI checks.
- Chrome's `scrollIntoView` returns a Promise: effects must use braces (`useEffect(() => { el?.scrollIntoView(...) })`), or React treats the return value as a cleanup function.
- The customer `ref` comes from the client. Customer scoping trusts it; there is no customer authentication yet.
- All ticket routes need a session (or `x-admin-token`) and are scoped to the account's repos; the customer chat
  is now an owner-only playground. Real customers reach Supfeel through the business's own agent over MCP.
- A ticket is billed when it opens: a turn that crashes afterwards is not refunded.
- Learning after a normal turn runs after the turn's `run` span has closed, so its "learn from ticket" span is not
  recorded (it is recorded on PR merge, inside the "pull request closed" run).
- Legacy `app/agent/events.py` `STEPS` lists the Velora steps; ticket steps are free-form names.
