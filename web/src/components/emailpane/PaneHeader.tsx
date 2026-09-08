import type { ReactElement } from 'react'
import { hashToHex } from '../../domain/ParticipantColor'

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
        <span className="chip" style={{ background: hashToHex(sessionUuid) }}>{sessionUuid}</span>
      </small>
    </div>
  )
}
