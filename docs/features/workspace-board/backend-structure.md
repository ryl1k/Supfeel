# Backend structure

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

```
backend/app/api/dashboard.py   DAYS (14), AUTOMATED, dashboard(p: CurrentPrincipal): 30-day stats, daily
                               series, by_category / by_status / by_channel, fixes, actions, learned,
                               onboarding flags, billing summary
backend/app/api/repos.py       _demo(settings): Slice demo offer (DEMO_GITHUB_REPO, or the bundled
                               examples/slice-pizza with ALLOW_LOCAL_REPOS + OPEN_IMPORT); github_status() returns it as `demo`
backend/app/main.py            _mount_demo_store(): mounts the Slice API at /demo-store when MOUNT_DEMO_STORE is on
backend/app/config.py          demo_github_repo, demo_store_dir, mount_demo_store
```
