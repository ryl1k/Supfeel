# Deployment (all free tiers)

| Part | Host | Config in repo |
|---|---|---|
| Database | **Neon** Free: Postgres 16 + pgvector | none (tables are created on boot) |
| Backend | **Render** free web service: Docker | `backend/Dockerfile`, `.dockerignore` |
| Frontend | **Vercel** Hobby | `frontend/vercel.json` (root directory `frontend`) |

Order: Neon → Render → Vercel → update the backend's CORS origins.

## 1. Neon

1. Create a project at console.neon.tech (pick a region close to your Render region, e.g. AWS us-east-1 ↔ Render Virginia, or eu-central-1 ↔ Render Frankfurt).
2. Copy the **pooled** connection string (`postgresql://…-pooler…neon.tech/neondb?sslmode=require`).
   The backend normalizes it for asyncpg and enables SSL automatically.
3. Nothing else is needed: on first boot the backend runs `CREATE EXTENSION vector`, creates tables, seeds the demo and embeds the knowledge base.

## 2. Render (backend)

1. dashboard.render.com → **New → Web Service** → connect GitHub → `ryl1k/Supfeel`.
2. Settings:

| Field | Value |
|---|---|
| Branch | `main` |
| Runtime / Language | **Docker** |
| Root Directory | *(leave empty: repo root)* |
| Dockerfile Path | `backend/Dockerfile` |
| Docker Build Context Directory | `.` |
| Instance Type | **Free** |
| Health Check Path | `/api/health` (Advanced) |

   The build context must be the repo root because the image copies `knowledge-base/`.
   Render injects `PORT`, and the container already listens on `${PORT}`.

3. Environment variables:

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
| `OPEN_IMPORT` | `false` in production (local-path imports stay disabled; GitHub imports need a signed-in workspace) |
| `DEMO_GITHUB_REPO` | e.g. `ryl1k/slice-pizza`: offered as the one-click demo in onboarding |
| `PUBLIC_APP_URL` | `https://<your-app>.vercel.app` (links in PR bodies and notifications) |
| `GITHUB_APP_ID`, `GITHUB_APP_SLUG`, `GITHUB_WEBHOOK_SECRET` | from the GitHub App (`docs/project/github-app-setup.md`) |
| `GITHUB_APP_PRIVATE_KEY_PATH` | `/etc/secrets/github-app.pem` with a **Secret File** named `github-app.pem` (Environment → Secret Files) |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | optional business notifications (also `SLACK_WEBHOOK_URL`, `DISCORD_WEBHOOK_URL`) |

4. **Create Web Service**. The first build takes a few minutes. Check
   `https://<service>.onrender.com/api/health` → `{"status":"ok","llm_mode":"live",…}`.

Boot (`python -m app.boot`) is idempotent: it seeds only an empty DB and re-embeds only changed KB chunks
(a full OpenAI ingest costs ≈ $0.0001). The image uses about 145 MB of the free 512 MB RAM.

### Free-tier sleep (important for the demo)

Free Render services **spin down after ~15 minutes without traffic**. The next request then takes 30–60 s to wake.
750 free instance-hours/month cover one service running 24/7, so keeping it awake is free:

- **Keep-alive ping**: a free monitor (e.g. UptimeRobot, 5-minute interval) on `https://<service>.onrender.com/api/health`.
  Turn it on before judging, and off afterwards if you like.
- Or at least open the site ~1 minute before presenting.

### After the first deploy

- MCP endpoint: `https://<service>.onrender.com/mcp`. Check it with
  `npx @modelcontextprotocol/inspector` (transport *Streamable HTTP*, header `Authorization: Bearer sf_live_…`).

- GitHub App → set the **Webhook URL** to `https://<service>.onrender.com/api/github/webhook`.
- Workspace → import your repo. For the Slice demo, push `examples/slice-pizza` to its own **public** repo (so CI on
  fix PRs is free), install the App on it, import it, then in the repo's Settings tab set
  *Business API base URL* `https://<service>.onrender.com/demo-store` and *Service token* `demo-service-token`.

## 3. Vercel (frontend)

1. Add New → Project → import `ryl1k/Supfeel`. **Root Directory: `frontend`**. Framework: Next.js (auto).
2. Environment variable: `NEXT_PUBLIC_API_URL = https://<service>.onrender.com` (no trailing slash).
3. Deploy, then put the Vercel URL into Render's `CORS_ORIGINS` (Render redeploys automatically on env changes).

## Operating the demo

- Reset demo data: the "Reset data" button in `/chat`, or `curl -X POST https://<api>/api/demo/reset`.
  Reset the Slice demo store: `curl -X POST https://<api>/demo-store/admin/reset`.
- Spend: `curl -H "x-admin-token: $ADMIN_TOKEN" https://<api>/api/admin/usage`.
- Kill switch: set `LLM_MODE=mock` on Render. The agent keeps working with the deterministic rule brain and $0 spend.
- Auto-deploy: Render redeploys on every push to `main` (sprint merges).
- Fallback hosts (same Dockerfile and variables): Koyeb free web service, or Hugging Face Spaces (Docker, port 7860).

## Local production check

```bash
docker build -f backend/Dockerfile -t supfeel-api .
docker run -p 8090:8000 -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5433/supfeel \
  -e LLM_MODE=mock supfeel-api
```
