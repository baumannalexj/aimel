// Presentational only. ErrorSurface decides when a banner exists; this just renders one.

import { ApiCallFailed } from '../../domain/ApiCallFailed'

export interface ErrorBannerProps {
  message: string
  cause?: unknown
  onDismiss: () => void
}

// status is 0 when the request never reached the api at all -- "status: 0" reads like a made-up
// code, so say the truer thing.
function statusLabel(status: number): string {
  return status === 0 ? 'unreachable' : String(status)
}

// The stack when there is one, or whatever the thrown value stringifies to when there isn't --
// an unexpected throw is exactly when you need something to expand.
function detailsOf(cause: unknown): string | undefined {
  if (cause === undefined) return undefined
  return cause instanceof Error ? cause.stack ?? String(cause) : String(cause)
}

export function ErrorBanner({ message, cause, onDismiss }: ErrorBannerProps) {
  const status = cause instanceof ApiCallFailed ? cause.status : undefined
  const details = detailsOf(cause)

  return (
    <div role="alert" className="error-banner">
      <div className="error-banner-content">
        {status !== undefined && (
          <span className="error-banner-status">status: {statusLabel(status)}</span>
        )}
        <span className="error-banner-message">{message}</span>
        {details && (
          <details className="error-banner-stack">
            <summary className="error-banner-stack-toggle">Stack trace</summary>
            <pre className="error-banner-trace">{details}</pre>
          </details>
        )}
      </div>
      <button type="button" className="secondary-button" onClick={onDismiss}>
        Dismiss
      </button>
    </div>
  )
}
