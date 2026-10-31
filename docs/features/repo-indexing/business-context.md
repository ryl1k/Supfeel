# Business context

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- Who: the business's admin. Import and re-index need the `x-admin-token` header unless `OPEN_IMPORT=true`;
  settings always need it.
- Limits protect the budget and the 512 MB Render instance: `REPO_MAX_FILES` (2000), `REPO_MAX_FILE_BYTES`
  (200 kB), `REPO_MAX_TOTAL_BYTES` (25 MB), tarball ≤ 120 MB (`MAX_TARBALL_BYTES`), `MAX_REPOS` (20).
- Claude spend per index job is capped by `INDEX_CAP_USD` (), and at most `REPO_MAX_MODULES_SUMMARIZED`
  (30, largest first) modules get a Claude summary. The rest get a rule-built summary.
- Never indexed: lockfiles, binaries, minified assets, vendored/build dirs, and secrets (`.env*`, `.npmrc`,
  `id_rsa`, `*.pem`, `*.key`…). See `source.keep_path`.
- Private repos need the GitHub App installed (or `GITHUB_TOKEN`); public repos also work anonymously.
- Local directories are only importable with `ALLOW_LOCAL_REPOS=true` (dev and tests).
