# Style guide

Four files, one entry point: `index.css` imports `tokens.css` → `base.css` → `components.css`, in
that order. Never import `base.css` or `components.css` on their own — tokens have to load first.

## Tokens (`tokens.css`)

All on `:root`, all consumed through `light-dark()`, so one declaration covers both color schemes.
`color-scheme: light dark` is set once at the top — don't repeat it elsewhere.

| Token | For |
|---|---|
| `--color-surface` | page/card background |
| `--color-surface-raised` | hover state, slightly-elevated panels |
| `--color-surface-sunken` | recessed areas (e.g. a selected/pressed background) |
| `--color-border` / `--color-border-strong` | default dividers vs. hover/focus emphasis |
| `--color-text` / `--color-text-muted` / `--color-text-subtle` | body copy → meta line → least-important label |
| `--color-accent` / `--color-accent-strong` | the one interactive hue — links, primary button, focus ring |
| `--color-accent-contrast` | text placed *on* an accent background |
| `--color-accent-muted` | accent-tinted background (selected row, badge) |
| `--color-notice-*` | non-error system messages, empty states |
| `--space-1`…`--space-8` | 4px grid: 4/8/12/16/24/32/48px |
| `--radius-sm/md/lg/full` | inputs & chips / buttons & cards / panels / pills |
| `--text-xs`…`--text-2xl` | type scale, base is 15px (dense, this is an inbox) |

Accent is violet, chosen because it sits outside the hues Paul Tol's qualitative palette uses for
per-session chips (teal, blue, orange, olive, yellow, pink). The one "do something" color should
never be mistaken for "this is session X."

## Primary vs. secondary button

- **Primary** (`.primary-button`): solid accent fill, white/near-black text depending on scheme.
  One per view, for the action the screen exists to accomplish — send, compose.
  Contrast-checked by hand (WCAG relative-luminance formula, not a tool): white-on-`#4a3fb8`
  ≈ 7.8:1 light mode, `#14121f`-on-`#ac9fff` ≈ 8.1:1 dark mode.
- **Secondary** (`.secondary-button`): outlined, surface background, normal text color. Everything
  else clickable — cancel, save draft, filters. No limit on how many appear in a view.

## Rules for future components

1. **No raw hex, no raw px in component CSS.** If a color or size isn't a token yet, add it to
   `tokens.css` first — don't inline a one-off value.
2. **One level of class nesting, max.** `.thread-row` and `.thread-row-title` are fine;
   `.thread-row .title .icon` is not. Flat classes stay greppable and don't fight specificity.
3. **Chips never hardcode a session's color.** `.chip` styles shape/padding/type only; background
   and text color are set inline by whatever assigns the per-session Tol color.

## Dark mode

Every color token resolves through `light-dark(light-value, dark-value)`, gated by the single
`color-scheme: light dark` declaration. There's no `@media (prefers-color-scheme)` block and no
`.dark` class to keep in sync — the browser picks based on OS setting, full stop.

## Contrast

Checked by hand against WCAG 2.1's relative-luminance formula, not measured with a tool:

| Pair | Ratio |
|---|---|
| body text on surface, light | ~17.2:1 |
| body text on surface, dark | ~15.2:1 |
| muted text on surface, light | ~7.2:1 |
| muted text on surface, dark | ~7.2:1 |
| notice text on notice bg, light | ~7.3:1 |
| notice text on notice bg, dark | ~8.7:1 |
| primary button text, light | ~7.8:1 |
| primary button text, dark | ~8.1:1 |

All comfortably clear the 4.5:1 floor. Take these as a sanity check, not a substitute for running
a real contrast checker before shipping.

## Deliberately left out

- No dark/light manual toggle in the app itself — `demo.html` has one only to preview both schemes
  without changing the OS setting.
- No animation/transition tokens yet — nothing in the app needs one.
- No `--color-danger` / error tokens — no destructive action exists yet to style.
- No component beyond what was asked for (no card, no modal, no input[type=text] styling
  distinct from textarea) — add them when a real screen needs them, not speculatively.
