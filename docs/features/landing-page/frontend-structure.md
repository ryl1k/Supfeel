# Frontend structure

> Status: **done** (Sprint 3). Paths below are real; keep them in sync with the code.

```
frontend/app/layout.tsx         Figtree (normal + italic, 300–700) via next/font, metadata, gem favicon
frontend/app/globals.css        design tokens (:root + Tailwind v4 @theme), .glass, .text-gradient, .btn-primary
frontend/app/page.tsx           BackgroundWaves + Nav + Hero, then Features, HowItWorks, About, FinalCta, Footer
frontend/components/landing/
  Nav.tsx          logo, anchor links (#features #about #how-it-works), outline "Try Supfeel →"
  Hero.tsx         3-line headline, subtitle, "Start chatting →" (to /chat), ChatPreview
  ChatPreview.tsx  static glass chat window built from components/chat/primitives.tsx
  Sections.tsx     Features, HowItWorks, About, FinalCta, Footer
frontend/components/brand/  Gem.tsx (logo/avatar), BackgroundWaves.tsx (SVG waves, masked fade-out)
frontend/public/gem.svg     round-brilliant sapphire mark (flat facets, no glow)
```
