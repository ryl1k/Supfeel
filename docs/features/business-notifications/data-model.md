# Data model

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

| Table | Columns |
|---|---|
| `notifications` | id, repo_id (FK repos, cascade), ticket_id (nullable, indexed, no FK), kind, title (≤ 300, includes the icon), body, url, delivered JSONB (`["telegram", "slack", "discord"]`), created_at |
