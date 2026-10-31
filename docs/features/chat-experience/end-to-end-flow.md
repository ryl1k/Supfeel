# End-to-end flow

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

1. User picks a demo customer → `conversation_id` created client-side (uuid).
2. Send message → `POST /api/chat` (SSE).
3. Render events: `step` → trail; `token` → streaming bubble; `action_proposed` → ConfirmCard;
   `action_done` / `verified` → ActionCard; `recommendations` → RecommendationCard.
4. Confirm → `POST /api/chat/confirm` (SSE continues the same turn).
5. `done` → enable composer.
