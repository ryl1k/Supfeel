# Ticket resolution

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

A customer opens a ticket on `/support/{repoId}`. A LangGraph graph gathers context from the indexed repo,
triages the ticket and routes it: **explain** a misunderstanding, **assist** (act through the business API),
**fix** a bug (Claude tool-use agent → PR), forward a **feature** request, **escalate**, or **ask** one
clarifying question. The reply streams over SSE. Closed tickets are embedded back into the index (learning).

## Why
This is the product: support that understands the actual code, acts, and verifies, instead of a FAQ bot.

## Scope
- In: ticket API + SSE stream, graph wiring, context gathering, triage (Claude or rules), customer reply,
  confirmation turns, yes/no feedback on explanations, learning, dashboard ticket list/detail.
- Out: the API-action authority rules (`assisted-actions`), the fix agent and CI loop (`code-fix-agent`),
  notifications (`business-notifications`), traces (`observability-traces`).

## Success criteria
- Every route works in `LLM_MODE=mock` (rule triage + rule reply); `backend/tests/support/test_tickets.py` is the contract.
- A turn completes and is persisted even if the customer closes the page.
- Similar past tickets show up in context for new tickets.
