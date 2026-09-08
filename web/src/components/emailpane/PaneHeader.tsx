import type { ReactElement } from 'react'

export class PaneHeaderProps {
  sessionUuid: string
  subject: string
  color: string

  constructor(sessionUuid: string, subject: string, color: string) {
    this.sessionUuid = sessionUuid
    this.subject = subject
    this.color = color
  }
}

export function PaneHeader({ sessionUuid, subject, color }: PaneHeaderProps): ReactElement {
  return (
    <div>
      <h2>{subject}</h2>
      <small className="meta">
        <span className="chip" style={{ background: color }}>{sessionUuid}</span>
      </small>
    </div>
  )
}
