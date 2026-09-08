// Presentational only. ErrorSurface decides when a banner exists; this just renders one.

export interface ErrorBannerProps {
  message: string
  onDismiss: () => void
}

export function ErrorBanner({ message, onDismiss }: ErrorBannerProps) {
  return (
    <div role="alert" className="error-banner">
      <span>{message}</span>
      <button type="button" className="secondary-button" onClick={onDismiss}>
        Dismiss
      </button>
    </div>
  )
}
