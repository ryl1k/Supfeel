# Known gotchas

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- **Embedding model switch = full re-embed.** `active_model()` returns `mock-hash-v1` whenever `LLM_MODE=mock`
  or `OPENAI_API_KEY` is empty, so flipping mock → live rebuilds every chunk. Search filters by
  `embedding_model`, so old-model chunks are invisible until the re-index finishes.
- Mock mode uses rule brains: summaries come from outlines + README (`rules_*`), `/ask` lists the top hits.
- Local repos only with `ALLOW_LOCAL_REPOS=true`. Their "sha" is `git rev-parse HEAD`, or a content hash outside git.
- Index jobs are in-process `asyncio` tasks. A deploy/restart kills them; boot marks them failed, so re-index by hand.
- A push during a running job does not start a parallel job. It sets `rerun_requested` and one follow-up runs at the end.
- Render free tier sleeps and GitHub gives webhooks 10 s: a push can be missed on a cold instance. Re-index manually or keep the service awake (`docs/project/deployment.md`).
- Modules beyond `REPO_MAX_MODULES_SUMMARIZED` get rule summaries, and they stay rule summaries until their input hash changes.
- The whole tarball is buffered in memory (≤ 120 MB) on a 512 MB instance; keep the repo limits conservative.
- `api_spec_url` changes need a re-index to take effect (settings save does not re-index).
- No migrations: new columns on existing DBs must be added by hand (`init_db` only creates missing tables).
