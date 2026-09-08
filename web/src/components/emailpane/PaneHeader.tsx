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

export function PaneHeader(_props: PaneHeaderProps): ReactElement {
  throw new Error('PaneHeader is not implemented yet')
}
