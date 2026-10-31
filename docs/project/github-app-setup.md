# GitHub App and integrations setup

Supfeel uses a **GitHub App** to read repositories (indexing), open fix pull requests, read CI results and
receive push webhooks (re-index on deploy). Everything here is free.

## 1. Create the app

github.com → Settings → Developer settings → **GitHub Apps → New GitHub App**
(or under an organization: Org settings → Developer settings → GitHub Apps).

| Field | Value |
|---|---|
| GitHub App name | e.g. `supfeel-bot` (must be globally unique; this becomes the slug) |
| Homepage URL | your Vercel URL (or `https://github.com/ryl1k/Supfeel`) |
| Callback URL | leave empty (no user OAuth needed) |
| Setup URL (optional) | `https://<your-app>.vercel.app/app?installed=1` |
| Webhook → Active | ✅ |
| Webhook URL | `https://<service>.onrender.com/api/github/webhook` |
| Webhook secret | a long random string (`openssl rand -hex 32`) |

### Repository permissions

| Permission | Access | Why |
|---|---|---|
| Contents | **Read and write** | download code for indexing, push fix branches |
| Pull requests | **Read and write** | open fix PRs |
| Issues | **Read and write** | file bug issues when no automatic fix is safe |
| Checks | **Read-only** | read CI results on fix PRs (verification) |
| Actions | **Read-only** | read workflow runs |
| Commit statuses | **Read-only** | CI providers that report statuses instead of checks |
| Metadata | Read-only | mandatory |

### Subscribe to events

`Push`, `Pull request`, `Check suite`, `Workflow run`, `Installation` events are delivered automatically.

"Where can this GitHub App be installed?": **Only on this account** is fine for the hackathon.

## 2. Collect the credentials

After **Create GitHub App**:

1. **App ID**: shown at the top of the app page.
2. **Private key**: "Generate a private key" downloads a `.pem` file.
3. **Slug**: the last part of the app URL (`github.com/apps/<slug>`).
4. The webhook secret you chose.

## 3. Install it

App page → **Install App** → choose your account → *Only select repositories* → pick the repo(s) Supfeel
should support (e.g. the demo target repo). Supfeel finds the installation per repo automatically.

## 4. Environment variables

Local: add to the repo-root `.env` (never committed). Render: Environment tab.

| Variable | Value |
|---|---|
| `GITHUB_APP_ID` | the App ID |
| `GITHUB_APP_SLUG` | the slug (used for the "Install app" link in the UI) |
| `GITHUB_APP_PRIVATE_KEY` | full PEM contents. On Render paste it as-is (multi-line is fine). In `.env` put it on one line with `\n` for newlines, or use `GITHUB_APP_PRIVATE_KEY_PATH` |
| `GITHUB_APP_PRIVATE_KEY_PATH` | local alternative: path to the `.pem` (keep it outside the repo, e.g. `~/.secrets/supfeel.pem`) |
| `GITHUB_WEBHOOK_SECRET` | the webhook secret |
| `GITHUB_TOKEN` | optional fallback: a fine-grained personal access token with the same repo permissions. Used only when no App is configured |
| `SLACK_WEBHOOK_URL` | optional: business notifications (bug found, PR opened, CI result) |
| `DISCORD_WEBHOOK_URL` | optional: same, for Discord |

Without any GitHub credentials, public repositories can still be imported and indexed (anonymous, read-only),
but Supfeel cannot open PRs; bug tickets then end as reports in the dashboard.

## 5. Notifications (optional, free)

- **Slack**: api.slack.com/apps → Create app → *Incoming Webhooks* → On → *Add New Webhook to Workspace* → pick a
  channel → copy the URL into `SLACK_WEBHOOK_URL`.
- **Discord**: channel settings → Integrations → Webhooks → New webhook → copy URL into `DISCORD_WEBHOOK_URL`.

All notifications are also stored and shown in the dashboard's business inbox, so this is not required.

## 6. Webhooks during local development

GitHub cannot reach `localhost`. Either test webhooks on the Render deploy, or use a free relay:

```bash
npx smee-client --url https://smee.io/<your-channel> --target http://localhost:8000/api/github/webhook
```

and set the app's Webhook URL to the smee channel while developing. Without webhooks, Supfeel still polls CI
status for its own PRs and you can re-index manually from the dashboard.

## 7. Demo target repository requirements

- **Public** (free GitHub Actions minutes) with a CI workflow that runs tests on `pull_request`.
- Ideally an OpenAPI spec (`openapi.json`/`openapi.yaml`) or a running API with `/openapi.json`, so Supfeel can
  act on customers' behalf (set the API base URL and service token in the repo's settings in the dashboard).
- Keep it under ~2,000 source files (indexing limit, protects the budget).
