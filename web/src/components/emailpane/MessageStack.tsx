import type { ReactElement, ReactNode } from 'react'
import type { Email } from '../../domain/Email'
import { Timestamp } from '../../domain/Timestamp'
import { AuthorPill, AuthorPillProps } from './AuthorPill'

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

// A flat list, not a tree. Indenting each older message implied a reply hierarchy the data does
// not have -- every message here is on one thread, not a reply to the one above it.
export function MessageStack({ emails, limit, slotAfterNewest }: MessageStackProps): ReactElement {
  const shown = emails.slice(0, limit)
  const hiddenCount = emails.length - shown.length

  return (
    <div className="message-stack">
      {shown.map((email, position) => (
        <div key={email.emailUuid}>
          <article className="message-stack-item">
            <header className="message-stack-item-header">
              <AuthorPill {...new AuthorPillProps(email.authorColor(), email.authorLabel())} />
              <small className="meta">{new Timestamp(email.sentAt).display()}</small>
            </header>
            {/* Our own agents' markup from a local database, so rendered as-is. */}
            <div className="message-stack-item-body" dangerouslySetInnerHTML={{ __html: email.bodyHtml }} />
          </article>
          {position === 0 && slotAfterNewest}
        </div>
      ))}
      {hiddenCount > 0 && (
        <p className="notice message-stack-overflow">
          {hiddenCount} earlier message{hiddenCount === 1 ? '' : 's'} not shown.
        </p>
      )}
    </div>
  )
}
