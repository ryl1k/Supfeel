# Frontend structure

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- `frontend/components/app/TraceView.tsx`: `TraceView({trace})`. `build()` links spans by `parent_id` into a
  tree (orphans become roots) and computes offsets. `FlowGraph` draws one row per root run with its child steps as
  arrow-linked cards (duration, cost, child-kind counts, errors). Below: kind filter chips, a waterfall
  (indent by depth, bar by start/duration, colour by `KIND_COLORS`), and `Attributes` for the selected span.
- Used in `TicketView.tsx` (polls the trace every 6 s while the ticket is live), `RepoView.tsx` Index runs
  (`api.jobTrace`) and Ask (`api.ticketTrace(answer.trace_id)`).
- Types `Span` / `Trace` in `frontend/lib/workspace.ts`.
