# Code-fix agent

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

For a ticket triaged as a bug, a Claude tool-use agent investigates the indexed code, decides whether it is
really a bug, makes the smallest fix plus a regression test in an in-memory overlay, and opens a pull request.
**The repository's own CI on that PR is the verification.** Merging the PR resolves the ticket, tells the
customer the fix is live, and feeds the ticket into learning.

## Why
Support tickets that are real bugs usually die in a backlog. Here the customer report becomes a reviewed,
tested PR within minutes, and the business only has to review and merge.

## Scope
- In: tool loop (`tool_turn`), Workspace overlay, protected paths, not-a-bug detection, publishing (PR or
  patch), re-applying edits on the fresh branch head, CI polling + webhook refresh, merge/close handling.
- Out: triage (`ticket-resolution`), GitHub auth and indexing (`repo-indexing`).

## Success criteria
- Never commits to the default branch; always a `supfeel/fix-<ticket>` branch and a PR for human review.
- Never edits CI config or secrets; at most 5 files.
- Without Claude (mock / cap) the ticket still becomes a useful bug report with suspect locations.
