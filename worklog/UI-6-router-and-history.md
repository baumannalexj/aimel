# UI-6 — real URLs, back and forward

Status: **done** — Router is a context provider (`useRoute`/`useNavigate`), not a page switch;
`InboxPage`/`ThreadPage` stay unused placeholders since App.tsx already had the real inbox/pane
logic and `pages/` was scaffolding for a data layer that never needed it.

Today thread selection is React state, not a URL. Nothing changes in the address bar, so back and
forward do nothing and a thread cannot be linked. That is the ticket.

Own `web/src/App.tsx`, `web/src/app/Router.tsx`, `web/src/app/routes.ts`. `Router.tsx` and
`routes.ts` already exist from earlier work and are **unwired** — App.tsx never imports them. Wire
them or rewrite them, your call, but the routes below are the contract.

## Routes

| path | behaviour |
|---|---|
| `/`, `/inbox`, `/emails` | all resolve to `/inbox` |
| `/emailthreads/<threadUuid>` | inbox on the left, that thread in the pane |
| `/emails/<emailUuid>` | inbox on the left, and the thread that email belongs to, newest message first |

Clicking a thread navigates to `/emailthreads/<threadUuid>` — it does not just set state.

## History

`pushState` on a thread click, so back returns to the previous thread and forward goes again.
`popstate` must re-render from the URL. Getting this wrong in the obvious way — pushing on every
render, or pushing while handling `popstate` — produces a history you cannot escape, so verify back
twice and forward twice, not once.

Do not add a router dependency. No installs. It is three route shapes.

## Depends on

`/emails/<emailUuid>` needs the thread uuid for an email, which is UI-7's job (it exposes
`threadUuid` on the email payload and adds the endpoint). Until it lands you can resolve a thread by
calling `openThread(emailUuid)`, which already returns an `EmailThread` carrying `threadUuid`.

## Done means

`npx tsc -b` exits 0. Verified against the real api on 8026: each route loads, a thread click changes
the address bar, back and forward both work twice over, and a cold load of a deep link renders that
thread.

**The Playwright MCP browser is shared and other agents navigate it out from under you** — two have
already hit this. Start your own `vite` on a free port in your worktree and drive it with a
Playwright browser you launch yourself, or verify by script, but do not trust the shared one.

Then set Status above to **done** with one line on anything you decided.
