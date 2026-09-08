import type { ErrorSeverity } from './ErrorSeverity'

// What the error surface needs to render a failure. Structural on purpose: anything with a message
// and a severity satisfies it.
export interface DisplayableError {
  message: string
  severity: ErrorSeverity
  /** The thrown value, when there was one, so the banner can show a status and a stack. */
  cause?: unknown
}
