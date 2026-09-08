// SEAM — props are settled, body is not. Ticket UI-3a.

import type { ReactElement } from 'react'

export class PaneHeaderProps {
  sessionUuid: string
  subject: string

  constructor(sessionUuid: string, subject: string) {
    this.sessionUuid = sessionUuid
    this.subject = subject
  }
}

export function PaneHeader({ sessionUuid, subject }: PaneHeaderProps): ReactElement {
  return (
    <div>
      <h2>{subject}</h2>
      <small className="meta">
        <span className="chip" style={{ background: 'var(--color-accent-muted)' }}>{sessionUuid}</span>
      </small>
    </div>
  )
}
