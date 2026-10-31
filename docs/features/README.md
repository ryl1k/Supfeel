# Feature context

AI needs business context. Every feature gets `docs/features/<feature>/` with **10 files**:

| Group | File | Contents |
|---|---|---|
| What and why | `FEATURE.md` | Main description: purpose, scope, success criteria |
| | `business-context.md` | Business rules and constraints |
| | `end-to-end-flow.md` | Step-by-step flow, including failure paths |
| Where it lives in code | `entry-points.json` | Entry points: HTTP routes, pages, CLIs, key modules, tests |
| | `per-app-responsibility.md` | What each app (backend, frontend, DB, external APIs) does |
| | `backend-structure.md` | Backend files and modules |
| | `frontend-structure.md` | Frontend routes and components |
| | `data-model.md` | Tables and types |
| Links and risks | `integration-points.md` | Where it touches other features and services |
| | `known-gotchas.md` | Known pitfalls |

New feature: `cp -r docs/features/_template docs/features/<name>`, fill in all 10 files, and add a row below.

## Features

| Feature | Status | Summary |
|---|---|---|
| [resolution-agent](resolution-agent/FEATURE.md) | done | LangGraph loop: understand → investigate → policy → plan → act → verify → respond |
| [business-tools](business-tools/FEATURE.md) | done | Mock Velora systems (Postgres) + read/write tools + demo reset |
| [knowledge-base-rag](knowledge-base-rag/FEATURE.md) | done | Chunk + embed `knowledge-base/` into pgvector; top-k retrieval |
| [llm-budget-guard](llm-budget-guard/FEATURE.md) | done | Single LLM gateway: caps, usage ledger, caching, mock/replay/live |
| [chat-experience](chat-experience/FEATURE.md) | done | `/chat` UI: streaming, action trail, confirmations, recommendations |
| [landing-page](landing-page/FEATURE.md) | done | `/` hero matching the design reference |

## Keeping it current

- When implementing: switch `Status` to in progress, and replace "planned" paths with real ones in `entry-points.json`.
- When a sprint ends: every feature touched has accurate structure files, plus new entries in `known-gotchas.md`.
