# Backend structure

> Status: **done** (Sprint 5, updated in Sprint 6). Paths below are real; keep them in sync with the code.

```
backend/app/repos/
  source.py    Snapshot; keep_path() filters (SKIP_DIRS, SKIP_FILES, BINARY_EXT, SECRET_NAMES); from_tarball(),
               from_directory(), fetch()
  chunker.py   language_for(), outline() (regex per language family), chunk_file() (~1800 chars, split at
               top-level defs / markdown headings, else 60-line windows with 8-line overlap)
  openapi.py   parse(), find_specs() (openapi|swagger|api-spec*.json|yaml), operations() ( inlining), fetch_spec(), describe()
  explain.py   MODULE_SYSTEM / OVERVIEW_SYSTEM prompts, group_modules(), module_input(), summarize_module/overview(),
               rules_module_summary(), rules_overview(), input_hash(), gather_limited() (4 concurrent)
  indexer.py   repo_id_for(), start_job() (job sets current_account from the repo), run_job(), recover_stale_jobs(), index_repo(), _index_api(), _explain()
  search.py    search(): pgvector cosine (k*3) + keyword boost (+0.15) for identifiers/paths; Hit.cite()
  ask.py       ask(), Answer schema, rules_answer()
  github.py    GitHub client (App installation tokens, PAT, anonymous), verify_signature(), client_for(), auth_mode()
backend/app/api/repos.py   HTTP routes (CurrentPrincipal + auth.repo_for scoping), payment_error() → 402,
                           delete_repo(), _demo() / github_status(), public_settings() masks api_token
backend/app/boot.py        recover_stale_jobs() on container start
```
