# Errors

The root container is the only place an error renders (see the "Errors" section of
`web/ARCHITECTURE.md`). Everything in this directory exists to make that true without every page
and component having to know about it.

## The rule

**No component outside this directory may render an error.** If a component catches something, it
reports it through `useErrorReporter()` (or lets it throw, for `ErrorBoundary` to catch) — it does
not put the message in a `<p>`, a `.notice`, or anywhere else itself.

## How the root container mounts this

```tsx
import { ErrorBoundary } from './app/errors/ErrorBoundary'
import { ErrorSurface } from './app/errors/ErrorSurface'

function RootContainer() {
  return (
    <ErrorSurface>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </ErrorSurface>
  )
}
```

`ErrorSurface` has to be the outer one: `ErrorBoundary` reads the reporter from the context
`ErrorSurface` provides, and if it's missing, the boundary logs to the console instead of silently
doing nothing.

## Reporting an error from anywhere below

Render-time throws are caught automatically by `ErrorBoundary`. Everything else — a failed fetch in
an event handler, a rejected promise — has to be reported explicitly:

```tsx
import { useErrorReporter } from './app/errors/ErrorSurface'
import { ErrorSeverity } from './app/errors/ErrorSeverity'

function SomePage() {
  const { reportError } = useErrorReporter()

  function onReplyFailed(cause: DomainException) {
    reportError({ message: cause.message, severity: ErrorSeverity.Transient })
  }
}
```

## Severity decides banner vs. toast

`ErrorSeverity.Blocking` gets the persistent red banner (the api is unreachable — nothing else on
the screen can be trusted until it's back). `ErrorSeverity.Transient` gets a toast that clears
itself after a few seconds (that one reply didn't send, but the rest of the app is fine). There's
one banner slot and a stack of toasts, not the other way around: a second blocking failure replaces
the first (they're both saying "nothing works right now"), but transient failures can pile up
independently.

## Wiring up the real `DomainException`

This was built before `DomainException` existed, so `ErrorSurface.reportError` takes a structural
`DisplayableError` — `{ message: string, severity: ErrorSeverity }` — rather than importing it.
Once `DomainException` lands, either:

- give it a `.severity` of type `ErrorSeverity` and pass it to `reportError` directly (it already
  satisfies the shape), or
- map at the catch site: `reportError({ message: e.message, severity: mapSeverity(e) })`.

`ErrorBoundary` always reports at `ErrorSeverity.Blocking`, since a render-time throw is a bug that
took down part of the screen, not a transient failure — that one isn't going through
`DomainException` at all.
