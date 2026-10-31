# Design system

Reference: `docs/design/landing-reference.png`. **Match this mock.** When in doubt, compare against it.

## Mood

Dark, calm, premium SaaS. A deep navy canvas with large, soft sapphire→indigo gradient waves sweeping from the top-right and bottom. Glassy translucent panels. Plenty of whitespace. Gemstone used **only** as the logo mark and the assistant avatar, nowhere else. No sparkles, lens flares or neon glow.

## Color tokens

| Token | Hex | Use |
|---|---|---|
| `--bg-0` | `#060A2B` | Page background (deepest navy) |
| `--bg-1` | `#0B1240` | Section / gradient base |
| `--sapphire-600` | `#2F3FE0` | Primary buttons, send button |
| `--sapphire-500` | `#4353F0` | Primary hover, links |
| `--indigo-400` | `#6B6FF2` | Gradient waves, accents |
| `--lavender-300` | `#A9ADF7` | Accent text (italic "truly helps"), highlights |
| `--lavender-200` | `#C9CBFA` | Secondary headline text ("AI support that") |
| `--text-100` | `#FFFFFF` | Primary text |
| `--text-300` | `#B8BCE0` | Muted body text |
| `--panel` | `rgba(30, 38, 110, 0.45)` | Glass panels (chat window) + `backdrop-filter: blur(16px)` |
| `--panel-bubble` | `rgba(55, 64, 150, 0.55)` | Chat bubbles |
| `--border` | `rgba(169, 173, 247, 0.22)` | 1px borders on panels, outline buttons, input |
| `--success` | `#3DDC84` | "Online" dot, verified status |
| `--warning` | `#F5B54A` | Needs confirmation |
| `--danger` | `#F26D7D` | Failed verification |

Background: `--bg-0` with 2–3 large blurred radial/linear gradient shapes in `--indigo-400` / `--sapphire-500` at low opacity, curving diagonally.

## Typography

- Font: geometric grotesk. Use **Figtree** (Google Fonts), falling back to `Inter`, then `system-ui`.
- Hero title "Supfeel": ~96px, semibold, white, tight letter-spacing (-0.02em).
- Hero line 2 ("AI support that"): ~80px, light/regular, `--lavender-200`.
- Hero line 3 ("truly helps"): ~80px, *italic*, `--lavender-300` → `--indigo-400` subtle gradient text.
- Subtitle: ~24px regular. The first phrase is white, the continuation is `--text-300`.
- Body: 15–16px. Chat text: 16px.

## Components

- **Nav**: logo (gem + "Supfeel" wordmark) left; centered links (Features, About, How it works) in `--text-300`; right **outline pill button** "Try Supfeel →" (1px `--border`, white text).
- **Primary CTA**: pill, `--sapphire-600` fill, white text + arrow, soft outer shadow (not glow), ~56px tall.
- **Chat window**: large rounded card (radius 28px), glass panel, 1px border. The header has a gem avatar, the name, a green "Online" dot and a `•••` menu, followed by a divider line.
- **Bubbles**: radius 20px. User bubbles are right-aligned with a circular person avatar on the right. Assistant bubbles are left-aligned with a gem avatar.
- **Rich card inside assistant turn**: e.g. "Personalized recommendations powered by Qloo", with a sparkle icon left, two-line text and a chevron right. The same pattern is used for **action cards** (Refund issued, Exchange created, Verified ✓).
- **Input**: pill, transparent with border, placeholder "Ask anything…", circular `--sapphire-500` send button on the right.

## Product-specific UI (beyond the mock)

- **Action trail**: compact timeline under assistant turns (Understand → Investigate → Plan → Act → Verify), each step with a status icon. Collapsible.
- **Confirmation card**: for sensitive actions, with Approve / Decline buttons.
- Keep everything in the same glass-panel language.

## Don'ts

- No heavy gem imagery, sparkles everywhere or neon glow.
- No pure-black backgrounds and no light theme for the demo.
- No more than one accent gradient per component.
