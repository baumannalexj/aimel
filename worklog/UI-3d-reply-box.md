# UI-3d — reply box

Status: **done** — body isn't cleared until `onSend` resolves, and stays intact on rejection too (the `finally` only resets the sending flag), so a failed send never loses what was typed.

Fill `web/src/components/emailpane/ReplyBox.tsx`. Props are settled; own that file only.

- Renders nothing when `open` is false.
- A textarea, a send button, a cancel that calls `onCancel`.
- `onSend(body)` is async and resolves once the reply is accepted. Disable send while it is in
  flight, and do not clear the textarea until it resolves — losing someone's typing on a failed
  send is the worst thing this component can do.
- Empty or whitespace-only body: send stays disabled. The api returns 422 for it, so this is just
  not making the user find out the slow way.
- Do not call the repository yourself. `EmailPane` owns that and passes `onSend`.

The trigger button and the placement between latest and latest-1 are already wired by `EmailPane`
and `MessageStack.slotAfterNewest` — you only build the box.

Done means `npx tsc -b` exits 0. Then set Status above to **done** with one line on anything you
decided.
