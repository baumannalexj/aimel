# UI-2 — click anywhere in the container, by composition

Status: **done** — Clickable/Card style themselves with inline styles off design tokens (no CSS file
edits); Clickable replicates hover/selected background in JS since inline styles can't do `:hover`.

Today a thread row is only clickable on a `<button>` around its subject. The whole row should be the
hit target.

Composition, not inheritance. `ThreadRow` becomes `Clickable` wrapping `Card` wrapping its content —
nesting, not `extends`.

## Fill the seams

`components/composition/Clickable.tsx` and `Card.tsx`. Signatures are settled.

`Clickable` must behave like a real button, because it is one: `role`, `tabIndex`, Enter **and**
Space, a visible focus ring, `aria-current` when `selected`. `label` exists for the accessible name —
the visible content is a row of chips and text, which reads as noise to a screen reader.

Do not nest a real `<button>` inside `Clickable`. That is invalid HTML and eats the outer click.

## Then apply it

Rewrite `components/ThreadRow.tsx` to use them, keeping what it renders identical: subject (bold when
unread), unread-count chip, session chip, email count, timestamp. Behaviour only.

## Done means

`npx tsc -b` exits 0. Verified in a browser: click lands from anywhere in the row including the
padding, Tab reaches it, Enter and Space both fire, focus is visible. Use an **isolated** Playwright
browser — the chrome-devtools MCP browser is shared with other agents running right now.
