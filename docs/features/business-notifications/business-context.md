# Business context

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

Notification kinds (`ICONS` in `support/notify.py`) and where they are emitted:

| Kind | Emitted by |
|---|---|
| `bug_reported` | `graph.fix_node` (patch / report), `graph.assist_node` (`also_bug`) |
| `pr_opened` | `graph.fix_node` (PR mode) |
| `ci_passed`, `ci_failed` | `ci.refresh` |
| `pr_merged` | `ci.on_pr_closed` |
| `action_taken` | `graph.act_node` (verified write) |
| `feature_request` | `graph.feature_node` |
| `escalation` | `graph.escalate_node`, `act_node` (failed verification), `service._drive` (crash), `service._close_answered` |

Channels are global (one set of env vars for the whole deployment), not per repository. Links point to
`PUBLIC_APP_URL` + `/app/tickets/{id}` or the PR URL.
