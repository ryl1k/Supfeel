# Frontend structure

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

- `frontend/app/app/page.tsx` → `components/app/Board.tsx`: greeting, Playground + "Add repository" buttons,
  `Checklist` (with `Ring`), `Kpi` tiles (tickets with MCP / playground split, % handled, fixes, credit),
  `DailyBars`, `CategoryBar` + verified actions / not-a-bug / learned, recent tickets (`TicketList`),
  activity (`NotificationItem`), `RepoCard`s, collapsible `ImportCard` + `GithubCard`.
- `components/app/Charts.tsx`: `CATEGORY_COLORS` (bug `#3987e5`, misunderstanding `#d95926`, assisted_action
  `#199e70`, feature_request `#c98500`, other `#d55181`; validated with the dataviz validator against the panel
  surface `#10164a`), `CATEGORY_LABEL`, `DailyBars` (single series, hover tooltip, max gridline),
  `CategoryBar` (stacked bar + legend with counts), `Ring` (progress).
- `frontend/app/app/welcome/page.tsx` → `components/app/Welcome.tsx`: 5-step wizard (`STEPS`), `Learning` (phases).
- `components/motion/Reveal.tsx` (adds `.is-visible` once via `IntersectionObserver`; `stagger` → `.reveal-stagger`),
  `components/motion/CountUp.tsx` (ease-out number animation; jumps straight to the value under reduced motion).
- `frontend/app/globals.css`: keyframes and utilities `.anim-fade-up/-fade-in/-scale-in/-pop/-float/-drift/
  -pulse-cta/-grow-x/-grow-y`, `.stagger`, `.reveal`, `.reveal-stagger`, `.lift`, `.skeleton`, `.page-enter`,
  `.flow-dash`, `.flow-dot`; all turned off in `@media (prefers-reduced-motion: reduce)`.
- Landing: `components/landing/ChatPreview.tsx` (escalation story), `EscalationFlow.tsx`, `Sections.tsx`
  (`Features`, `HowItWorks`, `Pricing`, `About`, `FinalCta`, `Footer`), `Nav.tsx` (`#pricing` link).
- Types: `Dashboard`, `GithubStatus.demo` in `frontend/lib/workspace.ts`.
