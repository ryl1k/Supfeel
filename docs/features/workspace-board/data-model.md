# Data model

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

No tables of its own. `GET /api/dashboard` response:

| Key | Meaning |
|---|---|
| window_days, tickets, automated, escalated_to_human | 30-day counters |
| by_category, by_status, by_channel | counts (`category` null → `other`; channel `web` / `mcp`) |
| daily | 14 × `{date, count}`, oldest first, UTC days |
| fixes | `{prs, ci_passed, patches, not_a_bug}` |
| actions | `{done, verified}` from `ticket_actions` |
| learned | tickets with `learned` |
| onboarding | `repo_imported, repo_ready, api_connected, key_created, first_ticket, first_mcp_escalation, payment_method, first_repo_id` |
| billing | `billing.summary()` or null (admin) |

`github_status.demo`: `{label, repo | local_path, api_base_url_path: "/demo-store", api_token, business_name: "Slice"}` or null.
