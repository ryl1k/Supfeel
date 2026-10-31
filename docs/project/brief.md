# Product brief: Supfeel

> Name inspired by *sapphire*. Tagline: **"More than answers — real solutions."**

## Problem

Customer support is mostly reactive. Customers explain their problem, get a generic answer, navigate a process themselves, and often bounce between departments before anything is fixed. Most "AI support" tools only shorten the answer step. They still hand the work back to the customer.

## Solution

Supfeel is an AI support agent that **takes responsibility for resolving the issue**. It moves on its own from understanding the problem to executing a fix and checking that the fix worked.

## Key capabilities

1. **Understand**: identify the customer's underlying problem, not just the literal question.
2. **Investigate**: gather data from connected business systems (customer profile, orders, shipments, payments, subscriptions).
3. **Reason and plan**: weigh possible resolutions against company policy (knowledge base) and choose an action plan.
4. **Act**: execute actions through tools/APIs (refund, exchange, reship, cancel, address change, store credit, escalate).
5. **Personalize**: tailor the solution to customer preferences where relevant (e.g. replacement product suggestions; Qloo optional).
6. **Verify**: confirm the problem is resolved by re-checking system state, then report back.

## Demo narrative

The demo store is **Velora**, a fictional online footwear and apparel retailer (policies in `knowledge-base/`).

Hero scenario (matches the landing mock):
> "I bought these sneakers, but they're uncomfortable. Can you help?"

Supfeel looks up the order and sees it was delivered 9 days ago, unworn-return eligible. It checks the return policy (30-day comfort guarantee) and asks what felt wrong (too narrow). It suggests a wide-fit alternative that matches the customer's style, creates an exchange, generates a return label, and verifies that the exchange order exists and the label is active. Then it summarizes the result with an action trail.

Secondary scenarios (to show breadth):
- **Late / lost package**: tracking shows stalled more than 7 days, so it reships or refunds per policy.
- **Double charge**: finds the duplicate payment and refunds it.
- **Subscription cancel / pause**: offers a pause first (retention), then cancels if the customer insists.
- **Out-of-policy request**: politely declines, explains why, offers the best allowed alternative, or escalates to a human.

## What makes it different (judging talking points)

- **Agentic, not chatty**: real tool calls change real (mock) system state.
- **Verification loop**: every action is followed by a read-back check.
- **Transparent**: the UI shows the plan, the tool calls and the verification status.
- **Policy-grounded**: decisions cite the knowledge base, so it doesn't invent policy.
- **Safe**: actions above set thresholds (e.g. refunds > $200) require confirmation or escalation.

## Open items

- Official hackathon name, organizer, rules and judging criteria are **not yet confirmed**. Do not invent them. Add them here once the user shares them.

## Brand

Deep navy, sapphire blue, indigo, subtle lavender. Modern minimal SaaS. **Avoid** excessive gemstones, shine and glow. See `design-system.md`.
