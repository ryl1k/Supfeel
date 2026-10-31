# Business context

> Status: **done** (Sprint 5, updated in Sprint 6). Paths below are real; keep them in sync with the code.

- PRs are opened only for GitHub repos with write access (GitHub App installation or `GITHUB_TOKEN`) and
  `settings.auto_fix` not `false` (default on). Otherwise the fix is kept as a **patch** on the ticket.
- Billing: each fix run is charged `fix` ($1.00) in `graph.fix_node` before `fixer.investigate()`; it is refunded
  (`billing.refund`) when the result is `report` (Claude unavailable / cap). Out of credit → the agent is skipped and
  `report_only()` runs ("Automatic fix skipped …").
- Limits: `FIX_MAX_TURNS` (16) agent turns, `FIX_CAP_USD` (1.50) per ticket under `conversation_id` `{ticket}:fix`, 4000 output tokens per turn,
  `effort="medium"`, at most 5 edited files, `PROTECTED` paths (`.github/`, `.env*`, `*.pem`, `*.key`).
- The agent must add or extend a regression test (`FIX_SYSTEM`); `finish` without edits is rejected.
- `not_a_bug` turns the ticket into an explanation (status `answered`) instead of a fix.
- CI polling: every `CI_POLL_SECONDS` (20 s), at most `CI_POLL_MAX` (45) times ≈ 15 minutes per PR; after
  `NO_CI_POLLS` (6) polls without any check (or at the end) the fix is marked unverified (`ci_missing` notification).
- Status changes after the turn (`fix_verified`, `fix_failed`, merge → `resolved`) fire the MCP callback (`callbacks.fire`).
- Merge → ticket `resolved` + customer message "the fix is now live". Closed unmerged → `escalated`.
- The customer never hears about PRs or code (`RESPOND_SYSTEM`); the business gets `pr_opened`, `ci_passed` /
  `ci_failed`, `pr_merged` notifications.
