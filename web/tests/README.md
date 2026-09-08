# tests

Mirrors `src/`. Two of these run today; the rest are skeletons.

## What runs now

`node --test src/domain/*.test.ts` — `Timestamp` and `ParticipantColor`. Node 24 strips TS natively,
so there is no runner to install.

## Why the rest are `.pending`

`node --test` can only test **leaf modules** — ones that import nothing relative. Node requires exact
import specifiers, and our app files import extensionlessly (`from './Actor'`). So the moment a test
imports `Email`, node fails to resolve `Email`'s own imports at runtime. It is not a typecheck
problem and no tsconfig fixes it.

Two ways out, both needing your approval to install:
- **vitest** — resolves through vite, so it already understands our imports and aliases. One dev
  dependency, and these `.pending` files become real tests by renaming them.
- **rewrite every relative import in `src/` with `.ts` extensions** — no dependency, but it touches
  every file and buys nothing else.

`Email.test.ts.pending` is the regression test for a real bug: the dashboard marked the newest email
read on open, including the human's own outgoing mail, which deleted it from the recipient's unread
queue before the agent polled. That is why a message sent from the app went unanswered. The fix is in
`App.tsx`; this file is the test that would have caught it.
