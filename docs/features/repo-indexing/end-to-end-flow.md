# End-to-end flow

> Status: **done** (Sprint 5, updated in Sprint 6). Paths below are real; keep them in sync with the code.

**Import** (`POST /api/repos`, body `{repo | local_path, branch?}`):
1. Check `MAX_REPOS` (counted per account). Local path: needs `ALLOW_LOCAL_REPOS` and admin or `OPEN_IMPORT` (403). Parse `owner/name` or a github.com URL; `client_for()` picks App → PAT → anonymous
   credentials; `get_repo` resolves the canonical name and default branch (404/502 with a hint for private repos).
2. Repo id from `repo_id_for()` plus the workspace's `__<acct6>` suffix (GitHub and local alike), so each workspace
   has its own connection to a repo. Charge `index` (402 on `PaymentRequired`), insert the `repos` row with `account_id` if new,
   then `indexer.start_job(trigger="import")`.

**Job** (`start_job` → background `run_job`, trace "index repository"):
1. If a job is already `queued`/`running` for the repo, set `progress.rerun_requested` and return its id (one follow-up run).
2. **download**: `source.fetch` → `branch_head` sha + one tarball (or `from_directory`) filtered by `keep_path` and limits.
3. **diff**: sha256 per file vs `repo_files.content_hash`. If no chunk exists for the active embedding model,
   treat everything as changed (full rebuild).
4. **update files**: delete stale `repo_files` / code+doc chunks; insert changed files with `outline()`.
5. **embed**: `chunk_file()` changed files, embed in batches of 200 (`node="repo_index"`), progress in `index_jobs.progress`.
6. **discover api**: `openapi.find_specs` in the repo + optional `settings.api_spec_url` (fetch failure is
   recorded on the span, never fails the job) → replace `api_operations` and `api` chunks.
7. **explain**: `explain.group_modules` (top two directory levels); regenerate only modules whose
   `input_hash` changed; Claude (`complete_text`, cap `INDEX_CAP_USD`) or `rules_module_summary`. Then the
   overview, skipped when its input hash is unchanged.
8. Write `repos.stats`, `head_sha`, `status=ready`. Job `done`; if `rerun_requested`, start a `push` job.

**Failure**: any exception → job `failed` with `error`, repo `status=failed`. On boot,
`recover_stale_jobs()` marks leftover `queued`/`running` jobs failed ("interrupted by a restart").

**Re-index**: `POST /api/repos/{id}/reindex` (charged `index`) or a GitHub `push` to the default branch (`api/github.py`, free).

**Delete**: `DELETE /api/repos/{id}` removes the repo; FKs cascade to files, chunks, docs, jobs, tickets, keys, notifications.

**Ask** (`POST /api/repos/{id}/ask`, charged `ask`; also MCP `ask_product`): `search(k=8)` → `complete_json(Answer)` with citations, or
`rules_answer` (top hits list) when Claude is unavailable. Trace id `ask_<hex>`.
