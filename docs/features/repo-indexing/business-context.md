# Business context

> Status: **done** (Sprint 5, updated in Sprint 6). Paths below are real; keep them in sync with the code.

- Who: the signed-in workspace owner. Repos belong to an account (`repos.account_id`); every per-repo route
  goes through `auth.repo_for` (404 for another workspace's repo). `x-admin-token` is an operator override.
- A GitHub repo can belong to one workspace only (409 "connected to another workspace").
- Billing: import and manual re-index are charged `index` ($0.10), `/ask` is charged `ask` ($0.02), up front
  (402 when out of credit or over the monthly limit). Push-triggered re-index is free.
- Limits protect the budget and the 512 MB Render instance: `REPO_MAX_FILES` (2000), `REPO_MAX_FILE_BYTES`
  (200 kB), `REPO_MAX_TOTAL_BYTES` (25 MB), tarball ≤ 120 MB (`MAX_TARBALL_BYTES`), `MAX_REPOS` (20, per workspace).
- Claude spend per index job is capped by `INDEX_CAP_USD` (), and at most `REPO_MAX_MODULES_SUMMARIZED`
  (30, largest first) modules get a Claude summary. The rest get a rule-built summary.
- Never indexed: lockfiles, binaries, minified assets, vendored/build dirs, and secrets (`.env*`, `.npmrc`,
  `id_rsa`, `*.pem`, `*.key`…). See `source.keep_path`.
- Private repos need the GitHub App installed (or `GITHUB_TOKEN`); public repos also work anonymously.
- Local directories are only importable with `ALLOW_LOCAL_REPOS=true` **and** either the admin token or
  `OPEN_IMPORT=true` (dev and tests). Their ids are namespaced per workspace (`local__name__<last 6 of account id>`).
