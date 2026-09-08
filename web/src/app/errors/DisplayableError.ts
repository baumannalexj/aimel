import type { ErrorSeverity } from './ErrorSeverity'

// The minimal shape this tier needs from a `DomainException` to render it. `DomainException`
// doesn't exist in this worktree yet (another agent owns web/src/domain/DomainException.ts), so
// this is a structural type: anything with a `message` and a `severity` satisfies it, including
// the real DomainException once it lands, without this file importing it.
export interface DisplayableError {
  message: string
  severity: ErrorSeverity
}
