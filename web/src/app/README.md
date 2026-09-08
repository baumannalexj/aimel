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

`routes.ts` holds the route table: a list of path patterns (`/`, `/inbox`, `/emails`,
`/emailthreads/:threadUuid`, `/emails/:emailUuid`) and, for each, a `build` function that turns
matched params into a typed `RouteMatch` (a discriminated union tagged by `name`:
`'inbox' | 'thread' | 'email' | 'not-found'`). `matchRoute(pathname)` runs the table and returns one
of those — never a loose record.

`Router` is a provider, not a page switch: it reads `window.location.pathname`, calls `matchRoute`,
and exposes the result plus a `navigate()` function through `useRoute()` / `useNavigate()`. It
listens for `popstate` to handle browser back/forward and re-match from the URL; `navigate(path)`
pushes a new entry via `history.pushState` and updates the route, without a full page reload. Callers
(`App.tsx`) decide what to render for each `RouteMatch` themselves — there is no `pages/` indirection,
since the inbox/thread views already need the live data layer, not a placeholder.

To add a route: add an entry to `routeTable` in `routes.ts` with its own `RouteMatch` variant, then
handle that variant wherever `useRoute()` is read.

`App.tsx` mounts `<Router>` at the root, inside the error boundary, and renders the inbox/thread pane
from `useRoute()` directly.
