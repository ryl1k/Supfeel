# Known gotchas

> Status: **done** (Sprint 5, updated in Sprint 6). Paths below are real; keep them in sync with the code.

- **Embedding model switch = full re-embed.** `active_model()` returns `mock-hash-v1` whenever `LLM_MODE=mock`
  or `OPENAI_API_KEY` is empty, so flipping mock → live rebuilds every chunk. Search filters by
  `embedding_model`, so old-model chunks are invisible until the re-index finishes.
- Mock mode uses rule brains: summaries come from outlines + README (`rules_*`), `/ask` lists the top hits.
- Local repos only with `ALLOW_LOCAL_REPOS=true` plus admin or `OPEN_IMPORT`; the same directory imported by two
  workspaces becomes two repos (namespaced ids). Their "sha" is `git rev-parse HEAD`, or a content hash outside git.
- Index jobs are in-process `asyncio` tasks. A deploy/restart kills them; boot marks them failed, so re-index by hand.
- A push during a running job does not start a parallel job. It sets `rerun_requested` and one follow-up runs at the end.
- Render free tier sleeps and GitHub gives webhooks 10 s: a push can be missed on a cold instance. Re-index manually or keep the service awake (`docs/project/deployment.md`).
- Modules beyond `REPO_MAX_MODULES_SUMMARIZED` get rule summaries, and they stay rule summaries until their input hash changes.
- The whole tarball is buffered in memory (≤ 120 MB) on a 512 MB instance; keep the repo limits conservative.
- `api_spec_url` changes need a re-index to take effect (settings save does not re-index).
- No migrations framework: `init_db` creates missing tables and runs a short `ADD COLUMN IF NOT EXISTS` list
  (e.g. `repos.account_id`); any other new column on an existing DB must be added there or by hand.
- Import is charged before the repo row and job exist; a failed job (or re-importing an existing repo) is not refunded.
- Repos created before Sprint 6 have `account_id` NULL: only the admin token sees them, and a workspace
  importing the same GitHub repo gets a 409.
- Repository ids are namespaced per workspace (`acme__shop__ab12cd`); `full_name` is not unique. Anything keyed on
  `full_name` (push webhooks, CI events, installation updates) must handle several rows. Rows created before this
  change keep their old ids (`ryl1k__supfeel`).
