# Frontend structure

> Status: **done** (Sprint 3). Paths below are real; keep them in sync with the code.

```
frontend/app/chat/page.tsx           background + <ChatApp/>
frontend/components/chat/
  ChatApp.tsx       layout: persona sidebar (horizontal chips on mobile) + glass chat window,
                    suggested prompts per persona, composer, reset demo, new conversation (••• button)
  primitives.tsx    avatars, UserBubble, AssistantRow/Bubble, InfoCard (shared with the landing preview)
  ActionTrail.tsx   collapsible step timeline: progress bar, live detail, policy citation chips, "offline reasoning" tag
  ActionCards.tsx   ConfirmCard (Approve/Decline), ActionResults (Verified badge + checks), RecommendationCard
  RichText.tsx      safe mini-markdown (paragraphs, bullets, **bold**)
frontend/lib/
  api.ts       fetch + manual SSE parser (POST), demo customers, reset, conversation ids
  useChat.ts   turn state machine: reduces SSE events into AssistantTurn objects
  types.ts     event + turn types (mirror of backend events)
```
