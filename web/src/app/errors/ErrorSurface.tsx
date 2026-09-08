import { createContext, useCallback, useContext, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { ErrorBanner } from './ErrorBanner'
import { ErrorSeverity } from './ErrorSeverity'
import { Toast } from './Toast'
import type { DisplayableError } from './DisplayableError'

export interface ErrorReporter {
  reportError: (error: DisplayableError) => void
}

// Not exported further than ErrorBoundary, which needs it to reach the reporter from a class
// component (no hooks there). Everything else should go through useErrorReporter.
export const ErrorReporterContext = createContext<ErrorReporter | null>(null)

export function useErrorReporter(): ErrorReporter {
  const reporter = useContext(ErrorReporterContext)
  if (!reporter) {
    throw new Error('useErrorReporter() called outside an ErrorSurface')
  }
  return reporter
}

interface ToastEntry extends DisplayableError {
  id: number
}

export interface ErrorSurfaceProps {
  children: ReactNode
}

// The root container mounts this once, above everything else. It is the only place an error
// actually renders: one banner for a blocking failure, a stack of toasts for transient ones.
export function ErrorSurface({ children }: ErrorSurfaceProps) {
  const [banner, setBanner] = useState<DisplayableError | null>(null)
  const [toasts, setToasts] = useState<ToastEntry[]>([])
  const nextToastId = useRef(0)

  const dismissBanner = useCallback(() => setBanner(null), [])

  const dismissToast = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const reportError = useCallback((error: DisplayableError) => {
    if (error.severity === ErrorSeverity.Blocking) {
      setBanner(error)
      return
    }
    const id = nextToastId.current++
    setToasts((current) => [...current, { ...error, id }])
  }, [])

  return (
    <ErrorReporterContext.Provider value={{ reportError }}>
      {banner && (
        <ErrorBanner message={banner.message} cause={banner.cause} onDismiss={dismissBanner} />
      )}
      {children}
      <div className="error-toast-stack">
        {toasts.map((toast) => (
          <Toast key={toast.id} message={toast.message} onDismiss={() => dismissToast(toast.id)} />
        ))}
      </div>
    </ErrorReporterContext.Provider>
  )
}
