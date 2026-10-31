# Deployment (all free tiers)

| Part | Host | Config in repo |
|---|---|---|
| Database | **Neon** Free: Postgres 16 + pgvector | none (tables are created on boot) |
| Backend | **Railway**: Docker | `railway.json`, `backend/Dockerfile`, `.dockerignore` |
| Frontend | **Vercel** Hobby | `frontend/vercel.json` (root directory `frontend`) |

Order: Neon → Railway → Vercel → update the backend's CORS origins.

## 1. Neon

1. Create a project at console.neon.tech (region close to Railway's, e.g. AWS us-east or eu-central).
2. Copy the **pooled** connection string (`postgresql://…-pooler…neon.tech/neondb?sslmode=require`).
   The backend normalizes it for asyncpg and enables SSL automatically.
3. Nothing else is needed: on first boot the backend runs `CREATE EXTENSION vector`, creates tables, seeds the demo and embeds the knowledge base.

## 2. Railway (backend)

1. New Project → Deploy from GitHub repo → `ryl1k/Supfeel`, branch `main`. Railway reads `railway.json` and builds `backend/Dockerfile` with the repo root as context.
2. Variables:

| Variable | Value |
|---|---|
| `DATABASE_URL` | Neon connection string |
| `ANTHROPIC_API_KEY` | your key |
| `OPENAI_API_KEY` | your key |
| `LLM_MODE` | `live` (or `mock` to demo with zero spend) |
| `CLAUDE_MODEL` | `claude-sonnet-5-5` |
| `LLM_BUDGET_HARD_CAP_USD` | `60` |
| `LLM_SESSION_CAP_USD` | `0.50` |
| `ADMIN_TOKEN` | a long random string |
| `CORS_ORIGINS` | `https://<your-app>.vercel.app` (set after step 3) |
| `CORS_ORIGIN_REGEX` | optional, e.g. `https://supfeel-.*\.vercel\.app` for preview deploys |

3. Settings → Networking → **Generate Domain**. Settings → **Serverless** (app sleeping) **on**, to stretch the free credit. The image uses about 145 MB of RAM.
4. Check: `https://<railway-domain>/api/health` → `{"status":"ok","llm_mode":"live",…}`.

Boot (`python -m app.boot`) is idempotent: it seeds only an empty DB and re-embeds only changed KB chunks
(a full OpenAI ingest costs ≈ $0.0001).

## 3. Vercel (frontend)

1. Add New → Project → import `ryl1k/Supfeel`. **Root Directory: `frontend`**. Framework: Next.js (auto).
2. Environment variable: `NEXT_PUBLIC_API_URL = https://<railway-domain>` (no trailing slash).
3. Deploy, then put the Vercel URL into Railway's `CORS_ORIGINS` and redeploy the backend.

## Operating the demo

- Reset demo data: the "Reset data" button in `/chat`, or `curl -X POST https://<api>/api/demo/reset`.
- Spend: `curl -H "x-admin-token: $ADMIN_TOKEN" https://<api>/api/admin/usage`.
- Kill switch: set `LLM_MODE=mock` on Railway. The agent keeps working with the deterministic rule brain and $0 spend.
- If the Railway trial credit runs out: the same Dockerfile runs on Render (free web service, Docker), with the same variables.

## Local production check

```bash
docker build -f backend/Dockerfile -t supfeel-api .
docker run -p 8090:8000 -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5433/supfeel \
  -e LLM_MODE=mock supfeel-api
```
