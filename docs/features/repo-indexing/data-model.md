# Data model

> Status: **done** (Sprint 5, updated in Sprint 6). Paths below are real; keep them in sync with the code.

| Table | Key columns |
|---|---|
| `repos` | id (`owner__name` / `local__name`, `local__name__<acct6>` for a workspace), account_id → accounts (cascade, nullable), full_name, source (`github`/`local`), local_path, default_branch, head_sha, installation_id, status (`pending`/`indexing`/`ready`/`failed`), error, overview, stats JSONB, settings JSONB, indexed_at |
| `repo_files` | repo_id, path, language, size, content_hash, content, outline JSONB `[{symbol, kind, line}]` |
| `repo_docs` | repo_id, kind (`overview`/`module`), key (module path, `.` for overview), title, body, input_hash, generated_by (`llm`/`rules`) |
| `repo_chunks` | repo_id, kind (`code`/`doc`/`summary`/`api`/`ticket`), path, symbol, start_line, end_line, text, content_hash, embedding_model, embedding vector(1536) |
| `api_operations` | repo_id, operation_id, method, path, summary, parameters JSONB, body_schema JSONB, source |
| `index_jobs` | id (`job_<hex>`), repo_id, kind (`full`/`incremental`), trigger (`import`/`manual`/`push`), status, commit_sha, progress JSONB, error, started_at, finished_at |

`repos.settings` keys: `api_base_url`, `api_token` (stored in plain text, masked in responses), `api_spec_url`,
`auto_fix`, `business_name`. All child tables (incl. `tickets`, `api_keys`, `notifications`) cascade on repo delete (`DELETE /api/repos/{id}`). `init_db()` (`backend/app/db/seed.py`) creates the HNSW index
`repo_chunks_embedding_hnsw` (cosine). Models: `backend/app/db/models.py`.
