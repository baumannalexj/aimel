# app

`Root` is the outermost shell: it takes `header`, `footer`, and `children` as already-rendered
nodes and lays them out. It knows nothing about product name, unread counts, or data.

`Header` and `Footer` are presentational, driven entirely by props (`HeaderProps`, `FooterProps`).
Neither fetches data or knows about the API — callers own that and pass values/nodes in.

Whoever wires the app (main entry) owns fetching data and deciding what goes in `rightSlot` and the
`children` slot; nothing in this folder should import `repository/` or `types/contract`.

`RootDemo.tsx` composes the three with placeholder content, to prove they render — not for wiring
into the running app.

## Router

`routes.ts` holds the route table: a list of path patterns (`/`, `/threads/:threadUuid`) and, for
each, a `build` function that turns matched params into a typed `RouteMatch` (a discriminated union
tagged by `name`: `'inbox' | 'thread' | 'not-found'`). `matchRoute(pathname)` runs the table and
returns one of those — never a loose record.

`Router.tsx` reads `window.location.pathname`, calls `matchRoute`, and renders the root page for
whichever variant comes back (`pages/InboxPage`, `pages/ThreadPage`, or an inline not-found node),
passing typed params as props. It listens for `popstate` to handle browser back/forward, and exposes
a `useNavigate()` hook — pages call `navigate(path)` to push a new URL via `history.pushState` and
re-render, without a full page reload.

`pages/` holds the root pages the table points at. Right now `InboxPage` and `ThreadPage` are
placeholders; the real inbox/thread views move in once the data layer restructure lands.

To add a route: add an entry to `routeTable` in `routes.ts` with its own `RouteMatch` variant, then
add a case in `Router.tsx`'s `renderRoute` that renders the corresponding page.

Nothing here is mounted yet — `App.tsx` still owns the running app. Wiring `Router` in is a
follow-up, done once the data layer it depends on is stable.
