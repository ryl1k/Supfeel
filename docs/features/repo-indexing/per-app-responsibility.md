# Per-app responsibility

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

| App | Responsibility |
|---|---|
| backend | Import, snapshot, chunk, embed, API discovery, summaries, search, ask; background jobs |
| Neon DB | `repos`, `repo_files` (full file content), `repo_docs`, `repo_chunks` (pgvector), `api_operations`, `index_jobs`, `spans` |
| GitHub | Repo metadata, branch head, tarball (one request per job), push webhooks |
| OpenAI | `text-embedding-3-small` for chunks (cached in `embedding_cache`) |
| Claude | Module summaries, overview, `/ask` answers (all optional; rules fallback) |
| frontend | Import form, repo cards with job progress, repo page tabs (overview, modules, ask, API, tickets, index runs, settings) |
