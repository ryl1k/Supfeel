# Integration points

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

- **accounts-billing**: `CurrentPrincipal` scoping; `billing.summary()` for the credit tile and onboarding card step.
- **mcp-server**: `api_keys` count (key step), `tickets.channel == "mcp"` (first escalation, KPI split); the
  wizard creates a key.
- **repo-indexing**: import / settings / repo polling in the wizard; `RepoCard`, `ImportCard`, `GithubCard`
  from `components/app/Workspace.tsx`.
- **ticket-resolution / code-fix-agent / assisted-actions**: ticket status, `fix`, `ticket_actions.verification`.
- **business-notifications**: activity feed (`api.notifications`).
- **landing-page**: `ChatPreview` and `EscalationFlow` replace the earlier hero story; design rules unchanged.
