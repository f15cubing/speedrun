# Readout — GRE Math visual identity (design spec)

_Date: 2026-07-05 · Status: approved (dashboard mock signed off) · Lane: fast (Qt-UI-only —
TS/Svelte/CSS + bundled font assets; no collection/undo/scheduler/proto/Rust touch)._

## Context

Finishing the UI redesign called for in `docs/ui-redesign-brief.md`. That effort decomposes into five
sub-projects; this spec covers **#1, the shared identity foundation**, plus its first application
(the hero dashboard). The others are follow-on sub-projects (each its own spec/plan):

1. **Shared identity foundation** *(this spec)* — tokens, type, the uncertainty signature. Lives in
   the dashboard route today (`anki/ts/routes/gre-dashboard/tokens.css` + `CalibrationStrip.svelte`).
2. 4A Dashboard (hero) — apply.
3. 4B Exam Mode — apply (keep clinical/austere per ETS).
4. 4C Interactive MCQ card — apply to the card face.
5. Deck-browser home — replace the uncommitted serif WIP with this identity.

The chosen direction is **Readout**: the app reads like a calibrated CAS/terminal printout. The
monospaced data face is the hero; every figure is a range in math notation that "shows its work".

## Constraints preserved (from the brief §5 — non-negotiable)

- Never a bare Readiness number (all seven evidence items together, or the give-up state).
- Never blend the three scores; each has its own range.
- Every metric is a range, never a lone point.
- Abstention is a **designed amber state**, never a red error.
- Light + dark, responsive (~360→960px), visible keyboard focus, `prefers-reduced-motion`, never
  encode meaning in color alone.
- **Offline**: fonts are bundled locally (no CDN); math stays MathJax/LaTeX.

## The one aesthetic risk

**Mono-as-hero everywhere** — title, eyebrows, labels, and all data are monospaced; prose is the only
non-mono text. Justified by the subject: numbers are the star, and a CAS printout is the honest
"instrument that shows its work" the product thesis wants. Intervals use math notation
(`∈ [0.54, 0.66]`) and carry a faint method tag (`Wilson`, `Platt`, `Poisson-binomial`).

## Token system

Typography (both **OFL**, bundled as local `woff2`, `font-display: swap`, system fallbacks):
- `--gre-mono` = **JetBrains Mono** — hero: title, eyebrows, labels, every number/range/percent/timer;
  `font-variant-numeric: tabular-nums` always.
- `--gre-sans` = **Inter** — body only: ledes, caveats, reasons, help copy.

Type scale (rem): eyebrow `0.64` / label `0.62` (tracked `0.16–0.24em`, uppercase) · body `0.92` ·
figure (point estimate) `1.15` · headline/title `1.9` (mono, tracking `-0.03em`).

Palette (6 core tokens + band/abstain-weak), **light / dark**:

| token | light | dark | role |
|---|---|---|---|
| `--gre-ink` | `#191a1a` | `#e6e7e9` | text |
| `--gre-muted` | `#6a6a68` | `#8b8f96` | secondary text |
| `--gre-faint` | `#9a9a97` | `#61656d` | method tags / n= |
| `--gre-surface` | `#ffffff` (bg `#fbfbfa`) | `#1b1e23` (bg `#14161a`) | surfaces |
| `--gre-sunk` | `#f0f0ee` | `#191c21` | strip tracks |
| `--gre-hairline` | `#dededb` | `#2a2e35` | rules/section dividers |
| `--gre-signal` | `#0a7d78` | `#34c0b8` | point tick / primary accent |
| `--gre-band` | `rgba(10,125,120,.15)` | `rgba(52,192,184,.20)` | confidence band |
| `--gre-abstain` | `#9c6200` | `#d59a3c` | abstain/give-up |
| `--gre-abstain-weak` | `rgba(156,98,0,.09)` | `rgba(213,154,60,.12)` | abstain fill |

`--gre-radius: 10px`, `--gre-gap: 1rem`. Dark values track Anki's `.night-mode` root class (as today).

## Signature — the "printout strip"

Evolves the existing `CalibrationStrip`, keeping its API and every honesty behavior:
- **Track** (0..max) with a shaded **band** (CI) + a **point tick** (signal). Empty (`n=0`) → dotted
  "not yet" rail (drawn, not hidden). `tone="abstain"` swaps to amber.
- **Readout is the hero**: `0.60  ∈ [0.54, 0.66]  n=238` in JetBrains Mono, tabular, with a faint
  right-aligned **method tag**. Values **column-align** across rows down the page (instrument log).
- **Motion**: one reduced-motion-safe reveal — bands draw in / values settle once on load.
- Reused at every scale (exam headline → 3 areas → 17 leaves) so "range, never a point" is the
  repeated visual language.

## Layout principles

Single centered column (~640px). Sections separated by **hairlines**, not heavy cards. Mono labels
left, tabular values right, column-aligned. The masthead = mono eyebrow + mono title + right-aligned
mono timestamp.

## Application to the hero dashboard (first surface)

- `tokens.css` — replace the current token values with the table above; add the two `@font-face`
  blocks (local woff2).
- `CalibrationStrip.svelte` — add the method-tag slot/prop, math-notation interval formatting, and
  column alignment; keep the empty/abstain/reduced-motion behavior and the `stripGeometry` lib.
- `MemoryPanel.svelte` / `ScoreSlot.svelte` / `CoverageMap.svelte` / `+page.svelte` — restyle to the
  printout layout (masthead, mono labels, aligned readouts, amber abstain slots, best-next ring).
  Pure presentation: **no** change to `dashboard_data.py` / the view-model / the no-fabrication guard.

## Cascade (later sub-projects, high level)

- **Exam Mode**: countdown → large JetBrains-Mono clock (amber < 5:00); item/options adopt the mono
  labels; results reuse the printout strip. Keep the ETS austerity.
- **MCQ card**: option letters + graded verdict in mono; correct/wrong keep green/red; light+dark.
- **Deck browser**: drop the serif WIP; New/Learn/Due as aligned mono columns; same masthead.

## Accessibility & offline

Contrast: signal/abstain on surface meet WCAG AA for text/UI; state is never color-only (labels +
`◀ best next` text + dotted rail carry meaning). Visible `:focus-visible` ring in `--gre-signal`.
`prefers-reduced-motion` disables the reveal. Fonts bundled locally; no runtime CDN.

## Testing / verification

- `check:svelte` + existing dashboard `lib.test.ts` (geometry unchanged) + any new formatter tests.
- Static headless render of the dashboard (light + dark) as the mock proved; the live in-app GUI
  click-through is the one human smoke step (offscreen QtWebEngine won't init headlessly).

## Task breakdown (implementation plan seed)

1. Bundle JetBrains Mono + Inter woff2 (subset) into the webview; wire `@font-face` in `tokens.css`;
   confirm offline serving via `mediasrv`.
2. Rewrite `tokens.css` to the Readout tokens (light + dark).
3. Evolve `CalibrationStrip.svelte` (method tag, math-notation interval, alignment) + tests.
4. Restyle the four dashboard components to the printout layout; verify `check:svelte` + headless
   light/dark render.
5. Ship as a fast-lane PR (self-review; 2–3 sentence intent). Then cascade sub-projects (exam / MCQ /
   deck browser), each its own spec + PR.

## Out of scope

Any change to scoring/view-model/collection; the other four surfaces' full implementations (they are
separate sub-projects that consume this foundation).
