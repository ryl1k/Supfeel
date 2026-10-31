# Business context

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

- Stats cover the last **30 days** of the workspace's repos (`window_days`); the daily series covers 14 days (`DAYS`).
- "Handled by Supfeel" = tickets whose status is in `AUTOMATED` (`answered`, `resolved`, `fix_in_review`,
  `fix_verified`, `reported`, `awaiting_confirmation`) over all tickets; `escalated` counts as handed to a human.
- Onboarding steps (`Board.steps`): import repo, repo ready, connect business API (optional), create an MCP key,
  first escalation (MCP or playground), add a card (optional). The checklist hides once all required steps are done.
- The one-click demo is the Slice pizza store: `DEMO_GITHUB_REPO` (a public GitHub copy, production) or, with
  `ALLOW_LOCAL_REPOS` and `OPEN_IMPORT`, the bundled `examples/slice-pizza` directory. It comes with the
  `/demo-store` API path and demo service token so the wizard can prefill the API step.
- Landing pricing mirrors `billing.PRICES` ($0.15 ticket, $1.00 fix run, $0.02 question, $0.10 index run) and
  the $5 welcome credit; both are hard-coded in the frontend.
- UI must match `docs/design/landing-reference.png` and `docs/project/design-system.md`.
