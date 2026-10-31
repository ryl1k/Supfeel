# End-to-end flow

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

**Signup → wizard** (`/app/welcome`, `Welcome.tsx`):
1. Polls `api.githubStatus()` (demo offer, App install URL) and `api.dashboard()` every 4 s. The current step is
   derived from progress (`auto`) unless the user clicks a step.
2. **Import**: GitHub URL or "Import Slice pizza demo" (`{repo}` or `{local_path}` from `status.demo`) →
   `POST /api/repos` (charged `index`). The wizard stays on **learn** and polls the repo every 2 s:
   phases download → embed (chunks done / total) → explain → ready, then shows stats and the overview.
3. **API**: base URL + service token → `PATCH /api/repos/{id}/settings`. For the demo it prefills
   `${API_URL}/demo-store` and the demo token and sets `business_name`. Skippable.
4. **Connect**: `POST /api/repos/{id}/keys` → one-time key + the Claude Code command.
5. **Try**: link to the playground `/support/{id}`; waits until `onboarding.first_ticket` turns true, then
   "You're set up" → board.

**Board** (`/app`, `Board.tsx`): polls `/api/dashboard` (8 s), `/api/me`, `/api/github/status`, repos (3 s
while indexing), tickets and notifications (10 s). `GET /api/dashboard`: repos of the account (all for admin),
tickets of the last 30 days, first-ticket / first-MCP-ticket probes, ticket actions, active key count, then
counters, `daily`, `fixes`, `actions`, `learned`, `onboarding` (+ `first_repo_id`, ready repo first) and
`billing` (null for admin). 401 without a session.

**Landing** (`/`): `Hero` → `ChatPreview` plays the story once (customer message → "Slice bot escalated to
Supfeel over MCP" → 4 steps → reply with workaround; CTA to `/signup`). `Features` → `EscalationFlow`
(customer → support bot → MCP → Supfeel → explain / act / fix → verified). `HowItWorks` (6 steps), `Pricing`,
wrapped in `Reveal` for scroll-in.
