# Demo script (≈ 4 minutes)

**Before:** Render awake (uptime ping or open `/api/health` a minute early), `LLM_MODE=live`, the Slice repo
imported and **Ready**, Settings → API base URL `https://<api>/demo-store` + token `demo-service-token`, and
`curl -X POST https://<api>/demo-store/admin/reset`. Have Telegram open on your phone.
Fallback: `LLM_MODE=mock` still runs every route (rules brains; bugs become reports instead of PRs).

## 0'. Setup in front of judges (optional, 60 s)
Get started → sign up → the wizard imports the Slice demo in one click, shows what Supfeel learned, pre-fills the
demo API, creates an MCP key and shows the `claude mcp add` line. Paste it into Claude Code on stage, then ask
Claude Code: "A Slice customer says checkout rejects 12 Oak St Apt #4B. Escalate it to Supfeel." Claude calls
`escalate`, streams progress, and relays the reply. The Board and the ticket's trace update live.

## 0. Hook (20 s)
"Support teams bounce customers between FAQs, agents and an engineering backlog. Supfeel has read your code, so it
knows whether the customer misunderstood, whether it can just do it for them, or whether the product is broken, and
then it fixes the code."

## 1. Import and understand (40 s)
Workspace → the Slice repo card → **Overview** (Claude explained the product, business rules, where to look) →
**Modules** → **API actions** (from the OpenAPI spec: what Supfeel can do for customers) → **Index runs** trace.
Mention: re-indexes on every push; only changed files are re-embedded.

## 2. Bug → verified fix (90 s, the hero)
Customer support page → **Maya** → "Checkout keeps saying 'Invalid address' for 12 Oak St Apt #4B".
- Step trail: Understand → Triage (*technical issue*) → Fix: the agent searches, reads `validation.py`, edits the
  regex, adds a regression test.
- Reply: apology + workaround ("write Apt 4B without the #"), no internals.
- Telegram buzzes: 🛠️ PR opened. Open the ticket page: root cause, diff, **PR link**, CI checks turn green → ✅ CI passed.
- (Optional) merge the PR on GitHub → ticket becomes **Resolved**, the customer gets "the fix is live", and the
  push re-indexes the repo.

## 3. Can't do it → we do it (45 s)
**New ticket** → **Jordan** → "The app crashes when I tap Reorder. Could you place my last order again for me?"
- Supfeel looks up Jordan's orders through the API and proposes *exactly* what it will send → **Approve** →
  **Verified** card: read back via `get_order`, every field matches. The crash is also reported to the business.

## 4. Misunderstanding (20 s)
"Why do I pay a delivery fee?" → explained from the code/docs (free from $25.00), "does that clear it up?" → "thanks" → resolved and learned.

## 5. Transparency + close (25 s)
Ticket page → **Trace**: the graph of steps, every Claude call (tokens, cache hits, cost), every search, API and
GitHub request. Inbox: everything the business was told.
Close: "Explain, act, or fix: verified every time. About $0.04 per ticket on Claude Sonnet with caching."
