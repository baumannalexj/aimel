# UI-5 — error banner with the stack

Status: **done** — after `DisplayableError` grew a `cause?: unknown` field, `ErrorBanner` takes `cause`
instead of separate `status`/`stack` and narrows it itself (`ApiCallFailed` for status, `Error` for
`.stack`, `String(cause)` as a last resort for anything else). Wired the one-line call site in
`ErrorSurface` and added `cause: error` to `ErrorBoundary`'s report so a render-time crash also gets a
stack, not just a message.

MVP error handling is deliberately blunt: the repository throws, nothing catches on the way up, the
root container shows a banner. Own `web/src/app/errors/ErrorBanner.tsx` and its styles.

The banner must show:
- `status: <n>` — from `ApiCallFailed.status`, which is `0` when the request never reached the api.
  Say something truer than "0" in that case.
- the message
- the **stack, behind an expander**, collapsed by default

`domain/ApiCallFailed.ts` carries `status`, `path` and `message`; it extends `DomainException` which
extends `Error`, so `.stack` is there.

Anything that is not an `ApiCallFailed` should still render — an unexpected throw is exactly when you
need the stack.

Do not build per-error-kind handling. The six `ResponseError` kinds and the `DomainException`
variants exist for V2; wiring them now is out of scope.

Done means `npx tsc -b` exits 0, and verified by making the api actually fail (stop the server on
8027, or point at a dead port) rather than by faking an error object. Isolated Playwright browser.
Then set Status above to **done** with one line on anything you decided.
