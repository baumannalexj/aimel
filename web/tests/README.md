# tests

Mirrors `src/`. Two of these run today; the rest are skeletons.

## What runs now

`node --test src/domain/*.test.ts` — `Timestamp` and `ParticipantColor`. Node 24 strips TS natively,
so there is no runner to install.

## Why the rest are `.pending`

The dividing line is **value imports vs type-only imports**, and it is sharper than "leaf modules".

Node requires exact import specifiers. Our app files import extensionlessly (`from './Actor'`), so
node cannot resolve them. But a *type-only* import (`import type { … }`) is erased before node ever
sees it, so a file whose relative imports are all type-only runs fine.

That is why `SessionOrdering.test.ts` can construct real `ClaudeSession` and `ThreadSummary`
objects — both import only types — while `Email.test.ts.pending` cannot:

```
Error [ERR_MODULE_NOT_FOUND]: Cannot find module '.../src/domain/Actor'
  imported from .../src/domain/Email.ts
```

`Email.ts` imports `Actor` and `parseEmailState` as *values*, so node must resolve them. No tsconfig
fixes this; it is a runtime resolution rule.

Two ways out, both needing your approval to install:
- **vitest** — resolves through vite, so it already understands our imports and aliases. One dev
  dependency, and these `.pending` files become real tests by renaming them.
- **rewrite every relative import in `src/` with `.ts` extensions** — no dependency, but it touches
  every file and buys nothing else.

`Email.test.ts.pending` is the regression test for a real bug: the dashboard marked the newest email
read on open, including the human's own outgoing mail, which deleted it from the recipient's unread
queue before the agent polled. That is why a message sent from the app went unanswered. The fix is in
`App.tsx`; this file is the test that would have caught it.
