# Per-app responsibility

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

| App | Responsibility |
|---|---|
| backend | Graph, triage, context, reply, persistence, learning, SSE |
| Neon DB | `tickets`, `ticket_messages`, `ticket_actions`, `notifications`, `spans`, `ticket` rows in `repo_chunks` |
| Claude | Triage (`ticket_triage`), reply (`ticket_respond`), assist planning, fix agent; all optional |
| OpenAI | Embeddings for context search and learned tickets |
| frontend | Customer chat (`/support/[repoId]`), dashboard ticket list and detail; no business logic |
