> **Main demo: Brewly.** A separate repo, `../brewly` (coffee subscriptions), has its own first-line bot that
> escalates to Supfeel over MCP. See `brewly/DEMO.md`. The Slice/chatbot case below is the alternative for showing
> Supfeel inside Claude Code or Claude Desktop.

# Demo case: "Slice Assistant" escalates to Supfeel

The story: **Slice** (a pizza-delivery app) has a basic first-line chatbot, "Slice Assistant". It knows the menu
and opening hours and nothing else. Behind it, over MCP, sits Supfeel, which has read Slice's code. You play the
customers; the chatbot escalates; Supfeel explains, acts, or fixes the code.

## 1. Setup (once, ~5 minutes)

1. Sign up → onboarding → **Import Slice pizza demo** (or import your public `slice-pizza` GitHub repo).
2. API step: base URL `http://localhost:8000/demo-store` (deployed: `https://<api>/demo-store`), token
   `demo-service-token`. The wizard pre-fills both for the demo.
3. Create an MCP key and add Supfeel to your chatbot:
   - **Claude Code**: `claude mcp add --transport http supfeel http://localhost:8000/mcp --header "Authorization: Bearer sf_live_…"`
   - **Claude Desktop**: the repo's Connect tab → "Claude Desktop" snippet (uses `mcp-remote`)
4. Reset the demo store before each run: `curl -X POST http://localhost:8000/demo-store/admin/reset`
5. For the PR part: the repo must be a GitHub repo with the Supfeel App installed (local imports produce a patch
   instead of a PR, which still demos well).

## 2. Paste this into the chatbot as its system prompt / instructions

```
You are "Slice Assistant", the first-line support chatbot of Slice, a pizza-delivery app.
You only know this:
- Menu: Margherita, Pepperoni, Funghi, Quattro Formaggi, Garden Veggie; sizes small, medium, large.
- Opening hours: 10:00–23:00.
For EVERYTHING else (bugs, errors, fees, orders, refunds, changes to an account, "can you do X for me"),
do not guess: escalate to Supfeel with the `escalate` tool. Pass:
- message: the customer's latest message, verbatim
- conversation: the conversation so far
- attempted: what you already tried (or "nothing, outside my knowledge")
- agent: "Slice Assistant"
- customer: the signed-in customer (below)
Then send the customer `customer_reply` exactly as returned.
If the result has `needs_confirmation`, ask the customer that question and pass their answer to `confirm`.
Never confirm on the customer's behalf. For follow-ups on the same issue use `reply` with the ticket_id.

The signed-in customer is: Maya Chen, customer id c_maya, maya@example.com.
```

For the scenarios marked **Jordan**, change the last line to:
`The signed-in customer is: Jordan Blake, customer id c_jordan, jordan@example.com.`
(Start a new chat when you switch customers.)

## 3. The scenarios: type these as the customer

| # | Customer | Type this | What Supfeel does | Show on screen |
|---|---|---|---|---|
| 1 | Maya | `Hi! What pizzas do you have?` | Nothing: the chatbot answers itself (menu). | The first-line bot handles the easy stuff. |
| 2 | Maya | `Why was I charged a delivery fee on my last order? I thought delivery was free.` | **Explains** from the code/docs: delivery is free from a $25.00 subtotal (after discounts), $3.99 otherwise. Asks if that clears it up. Reply `thanks, that helps` → resolved and learned. | Ticket: *Explanation*. Trace: search hits in `pricing.py` / FAQ. |
| 3 | Jordan | `The app crashes every time I tap Reorder. Can you just place my last order again?` | **Acts**: looks up Jordan's orders through the API, proposes repeating order `o_1001` (large Pepperoni + medium Margherita). Chatbot asks for confirmation. Reply `yes please` → order placed, **verified by read-back** (8 checks). Also reports the crash to engineering. | Ticket: *Assisted action → Resolved*. Inbox: "Done for customer" + "Possible bug". Telegram buzzes. |
| 4 | Jordan | `Actually, cancel that order, I'll order later.` | **Acts** again: proposes cancelling the new order; on `yes` it cancels, refund to the original payment, verified. | Actions card: `POST /orders/{id}/cancel`, verification checks. |
| 5 | Maya | `I'm trying to order to 12 Oak St Apt #4B but checkout keeps saying "Invalid address". I can't order!` | **Fixes**: the fix agent searches the checkout code, finds the root cause (the `_STREET` regex rejects `#`), edits `slice_api/validation.py`, adds a regression test, opens a **pull request** (GitHub) or prepares a patch (local). Customer gets an apology and a workaround: "enter Apt 4B without the #". | Ticket: root cause, diff, PR link, CI checks turning green → *Fix verified*. Telegram: 🛠️ PR opened → ✅ CI passed. |
| 6 | Maya | `Please cancel order o_1001.` | **Refuses safely**: `o_1001` is Jordan's order; the ownership check (in code, not the prompt) blocks it and hands over to a human. | Trace: blocked by the safety rules. |
| 7 | Maya | `It would be great if you had a gluten-free crust option!` | **Feature request**: thanks the customer, notifies the product team. | Inbox: 💡 Feature request. |
| 8 | Maya (new chat) | `Your checkout says my address 5/2 King Rd is invalid` | Same bug family (`/` in unit numbers). Supfeel finds the **similar past ticket** from scenario 5 in its context. | Trace → context step: "1 similar past ticket". |

Optional closer: merge the PR on GitHub → the ticket becomes **Resolved**, the customer is told the fix is live, the
push **re-indexes** the repo, and the chatbot's `callback_url` (if you passed one) receives the update.

## 4. What to point at while it runs

- **Board** (`/app`): tickets per day, "what customers needed", handled-by-Supfeel %, credit.
- **Tickets** (`/app/tickets`): cards move from "With the customer" to "With engineering" to "Fix verified" / "Resolved".
- **Ticket page**: conversation (including the first-line bot's messages), engineering card (root cause, diff,
  PR, CI), actions with verification checks, and the **trace graph**: every step, Claude call (tokens, cache hits,
  cost), code search, API and GitHub call.
- **Billing**: each escalation $0.15, fix run $1.00, from the $5 welcome credit.

## 5. Timing and cost

| Scenario | Time | Claude cost |
|---|---|---|
| Explain (2) | ~10 s | ~$0.01 |
| Act (3, 4) | ~15–25 s each | ~$0.03 |
| Fix (5) | ~40–90 s (plus CI ~1 min) | ~$0.04–0.10 |
| Whole run | ~5 min | ~$0.25 |

## 6. If something goes wrong

- Chatbot answers instead of escalating → remind it: "escalate this to Supfeel".
- "Not enough credit" / "Monthly spend limit" → Billing → add credit (mock card `4242 4242 4242 4242`).
- Reorder proposes an odd order → reset the store (setup step 4) and start a new chat.
- Claude unavailable → set `LLM_MODE=mock`: every route still works (rules), bugs become reports instead of fixes.
