import { Component } from 'react'
import type { ContextType, ReactNode } from 'react'
import { ErrorReporterContext } from './ErrorSurface'
import { ErrorSeverity } from './ErrorSeverity'

export interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
}

// Catches render-time throws below it in the tree and hands them to the ErrorSurface instead of
// rendering anything itself — this component decides that something broke, not how to show it.
// React error boundaries have to be class components; componentDidCatch has no hooks equivalent.
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  static contextType = ErrorReporterContext
  declare context: ContextType<typeof ErrorReporterContext>

  state: ErrorBoundaryState = { hasError: false }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true }
  }

  componentDidCatch(error: Error): void {
    if (this.context) {
      this.context.reportError({ message: error.message, severity: ErrorSeverity.Blocking })
    } else {
      // No ErrorSurface above it is a setup bug, not a user-facing failure — don't hide it.
      console.error('ErrorBoundary caught an error with no ErrorSurface mounted above it:', error)
    }
  }

  render(): ReactNode {
    // The crashed subtree is gone either way; the banner (or the console, above) carries the news.
    return this.state.hasError ? null : this.props.children
  }
}
