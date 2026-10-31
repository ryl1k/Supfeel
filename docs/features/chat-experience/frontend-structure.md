# Frontend structure

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

```
frontend/app/chat/page.tsx
frontend/components/chat/
  ChatWindow.tsx          glass card: header (gem avatar, "Online"), list, composer
  MessageBubble.tsx       user (right, person avatar) / assistant (left, gem avatar)
  ActionTrail.tsx         Understand → Investigate → Policy → Plan → Act → Verify
  ActionCard.tsx          refund/exchange/label result + verified badge
  ConfirmCard.tsx         Approve / Decline
  RecommendationCard.tsx  sparkle icon, 2 lines, chevron (mock: "powered by Qloo")
  Composer.tsx            pill input "Ask anything…", round send button
  CustomerPicker.tsx
frontend/lib/  sse.ts  api.ts  types.ts
frontend/styles/tokens.css  (design tokens from docs/project/design-system.md)
```
