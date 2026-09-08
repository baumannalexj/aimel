// SEAM — props are settled, body is not. Ticket UI-3c.

import type { ReactElement } from 'react'

export class AuthorPillProps {
  emailAddress: string
  label: string

  constructor(emailAddress: string, label: string) {
    this.emailAddress = emailAddress
    this.label = label
  }
}

export function AuthorPill(_props: AuthorPillProps): ReactElement {
  throw new Error('AuthorPill is not implemented yet')
}
