// SEAM — props are settled, body is not. Ticket UI-3b.

import type { ReactElement, ReactNode } from 'react'
import type { Email } from '../../domain/Email'

export class MessageStackProps {
  /** Newest first, exactly as the api sends them. */
  emails: Email[]
  limit: number
  /** Rendered between the newest message and the one below it, when present. */
  slotAfterNewest?: ReactNode

  constructor(emails: Email[], limit: number, slotAfterNewest?: ReactNode) {
    this.emails = emails
    this.limit = limit
    this.slotAfterNewest = slotAfterNewest
  }
}

export function MessageStack(_props: MessageStackProps): ReactElement {
  throw new Error('MessageStack is not implemented yet')
}
