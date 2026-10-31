# Frontend structure

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

```
frontend/app/layout.tsx        Figtree font, tokens, background gradient waves
frontend/app/page.tsx          composes sections
frontend/components/landing/
  Nav.tsx  Hero.tsx  ChatPreview.tsx  Features.tsx  HowItWorks.tsx  About.tsx  Footer.tsx
  BackgroundWaves.tsx          SVG/CSS gradient shapes
frontend/public/gem.svg        logo + avatar mark
```
`ChatPreview` reuses `MessageBubble` / `RecommendationCard` from `components/chat/` for consistency.
