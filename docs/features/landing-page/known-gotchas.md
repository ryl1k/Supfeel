# Known gotchas

> Status: **done** (Sprint 3). Paths below are real; keep them in sync with the code.

- Gradient waves: use large blurred SVG paths, not many stacked box-shadows (perf).
- Italic "truly helps" needs Figtree italic weights loaded explicitly via `next/font`.
- Keep the gem asset small (SVG); no PNG gemstones or glow filters.
- The recommendation card says "matched to your style and fit", **not** "powered by Qloo": Qloo isn't integrated, and the UI must not claim it is.
- Headless Chrome has a minimum window width (~500px). For mobile screenshots, render the page in a 390px iframe or use puppeteer viewport emulation.
- Next 16 + `cacheComponents`: anything random/time-based (e.g. `crypto.randomUUID()`) during render fails the prerender. Do it in event handlers or effects.
