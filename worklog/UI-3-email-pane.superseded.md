# UI-3 — the email pane

Threads list stays on the left. This is the right pane, for one thread. Own
`components/emailpane/*`; do not edit `app/pages/*` (UI-4) or `components/ThreadRow.tsx` (UI-2).

## Header

- The AI session's **full** uuid, not the 8-char short form. The short one is for the narrow list.
- The subject below it.

## Message stack

Newest message first, then each older one nested one level deeper, **limit 5**:

```
latest
  latest-1
    latest-2
      ...
```

Each message shows its author pill, `new Timestamp(email.sentAt).display()`, and its body.

Pill colour is `participantColor(email.sender)` — everyone including the human, same function. Both
seams are in `domain/`; code against the signatures, they will not change. UI-1 is filling the bodies
in parallel, so `display()` and `hashToHex` throw until it lands: build against them anyway and
verify once UI-1 reports, or stub locally in your own scratch file — do not edit their two files.

The existing per-session chip stays as it is. That marks which session the thread belongs to; these
new pills mark who wrote each message. Two different questions.

## Reply

- Trigger at the **top right** of the pane.
- The compose box opens **between the latest message and latest-1**, not at the bottom. You are
  answering the newest message, so that is where the reply belongs.
- Submit through the repository: `repository.replyTo(emailUuid, body)`, which returns the reloaded
  thread. Take the repository as a prop; never import the client, `Result`, or a `*Response`.

## Done means

`npx tsc -b` exits 0. Rendered in a browser against the real api on 8027, with a thread of 7+ emails
so the 5 limit actually truncates. Use an **isolated** Playwright browser — the chrome-devtools MCP
browser is shared with other agents right now. Sending a real reply is fine; prefix the body
`[UI-3 TEST]`.
