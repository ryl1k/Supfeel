# Chat experience

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

The customer-facing chat: glass chat window from the landing mock, streaming replies, a visible
action trail, confirmation cards for sensitive actions, and recommendation cards.

## Why
Judges must *see* the agent think and act. Transparency is the differentiator vs. a plain chatbot.

## Scope
- In: `/chat` page, SSE client, message list, action trail, confirm/decline, recommendation card,
  demo customer picker, error/budget states.
- Out: landing page (see `landing-page`), agent logic.

## Success criteria
- Matches `docs/design/landing-reference.png` chat window styling.
- Every agent step and action is visible within 300 ms of the event.
