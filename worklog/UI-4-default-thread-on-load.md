# UI-4 — open the newest thread on load

Today the app loads to an empty right pane and the user has to click something before seeing mail.
Load the newest thread instead.

Own `app/pages/*` and the container that fetches. Do not edit `components/emailpane/*` (UI-3) or
`components/composition/*` and `ThreadRow.tsx` (UI-2).

- `listInbox()` already returns threads newest-first. Take the first one and open it via
  `openThread(latestEmailUuid)`.
- The left list stays; that thread shows as selected.
- Empty inbox: no crash, no spinner forever, say there's no mail.
- The deep link wins. If the route already names a thread, open that one — a default must never
  overwrite an explicit request.

Everything goes through `EmailRepository`. The root container constructs it; pages receive it. Never
import the client, `Result`, or a `*Response`.

## Done means

`npx tsc -b` exits 0. Verified in a browser against the real api on 8027: a cold load lands on the
newest thread with its emails rendered and no click; the empty case behaves. Use an **isolated**
Playwright browser — the chrome-devtools MCP browser is shared with other agents right now.
