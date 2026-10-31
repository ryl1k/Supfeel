# Data model

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

`tickets.fix` JSONB (set by `fixer.publish`, updated by `ci.refresh`):

| Key | Meaning |
|---|---|
| decision | `fixed` / `not_a_bug` / `gave_up` / `report` |
| mode | `pr` or `patch` (absent when not fixed) |
| root_cause, summary, test, confidence, workaround, explanation, note | agent output / reason for patch mode |
| files, diff | touched paths; unified diff vs the indexed version (≤ 60 kB) |
| suspects | `path:start-end` cites (report mode) |
| branch, head_sha, pr_number, pr_url | PR mode |
| ci | `{state: none/pending/success/failure, checks: [{name, status, conclusion, url}]}` |

Ticket statuses used here: `fix_in_review`, `fix_verified`, `fix_failed`, `reported`, `resolved`, `escalated`.
