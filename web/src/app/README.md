# app

`Root` is the outermost shell: it takes `header`, `footer`, and `children` as already-rendered
nodes and lays them out. It knows nothing about product name, unread counts, or data.

`Header` and `Footer` are presentational, driven entirely by props (`HeaderProps`, `FooterProps`).
Neither fetches data or knows about the API — callers own that and pass values/nodes in.

Whoever wires the app (main entry) owns fetching data and deciding what goes in `rightSlot` and the
`children` slot; nothing in this folder should import `repository/` or `types/contract`.

`RootDemo.tsx` composes the three with placeholder content, to prove they render — not for wiring
into the running app.
