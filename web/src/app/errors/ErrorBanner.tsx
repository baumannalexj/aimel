// Presentational only. ErrorSurface decides when a banner exists; this just renders one.

export interface ErrorBannerProps {
  message: string
  status?: number
  stack?: string
  onDismiss: () => void
}

// status is 0 when the request never reached the api at all -- "status: 0" reads like a made-up
// code, so say the truer thing.
function statusLabel(status: number): string {
  return status === 0 ? 'unreachable' : String(status)
}

export function ErrorBanner({ message, status, stack, onDismiss }: ErrorBannerProps) {
  return (
    <div role="alert" className="error-banner">
      <div className="error-banner-content">
        {status !== undefined && (
          <span className="error-banner-status">status: {statusLabel(status)}</span>
        )}
        <span className="error-banner-message">{message}</span>
        {stack && (
          <details className="error-banner-stack">
            <summary className="error-banner-stack-toggle">Stack trace</summary>
            <pre className="error-banner-trace">{stack}</pre>
          </details>
        )}
      </div>
      <button type="button" className="secondary-button" onClick={onDismiss}>
        Dismiss
      </button>
    </div>
  )
}
