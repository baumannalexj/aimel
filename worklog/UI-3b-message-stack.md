# UI-3b — nested message stack

Status: **not started**

Fill `web/src/components/emailpane/MessageStack.tsx`. Props are settled; own that file only.

Newest first, each older message nested one level deeper, stopping at `limit` (5):

```
latest
  latest-1
    latest-2
      ...
```

- Each message shows its author pill (`<AuthorPill>`, UI-3c owns it — import and use it), the
  timestamp via `new Timestamp(email.sentAt).display()`, and the body.
- `slotAfterNewest` renders between the newest message and latest-1. That is where the reply box goes.
- Past `limit`, say how many are hidden rather than truncating silently.
- Indentation must not run off-screen on the 5th level. Cap the indent or switch to a subtler marker.

`Timestamp.display()` and `AuthorPill` throw until UI-1 and UI-3c land — build against them anyway.
Do not edit their files.

Done means `npx tsc -b` exits 0, and rendered against a thread of 7+ emails on the real api (8027)
so the limit actually truncates. Isolated Playwright browser, not the shared chrome-devtools one.
Then set Status above to **done** with one line on anything you decided.
