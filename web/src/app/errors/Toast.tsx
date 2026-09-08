import { useEffect } from 'react'

// Transient failures clear themselves; the user shouldn't have to dismiss every one by hand.
const AUTO_DISMISS_MS = 5000

export interface ToastProps {
  message: string
  onDismiss: () => void
}

export function Toast({ message, onDismiss }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, AUTO_DISMISS_MS)
    return () => clearTimeout(timer)
  }, [onDismiss])

  return (
    <div role="status" className="error-toast">
      <span>{message}</span>
      <button type="button" className="secondary-button" onClick={onDismiss}>
        Dismiss
      </button>
    </div>
  )
}
