// SEAM — props are settled, body is not. Ticket UI-3b.

import type { CSSProperties, ReactElement, ReactNode } from 'react'
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

// The indent is a "how deep are we" cue, not a ruler -- past this depth it stops growing and
// the connecting line does the rest of the work, so five levels never run off a narrow pane.
const MAX_INDENT_DEPTH = 3

export function MessageStack({ emails, limit, slotAfterNewest }: MessageStackProps): ReactElement {
  const shown = emails.slice(0, limit)
  const hiddenCount = emails.length - shown.length

  return (
    <div className="message-stack">
      {shown.map((email, depth) => (
        <div key={email.emailUuid} className="message-stack-level" style={{ '--depth': Math.min(depth, MAX_INDENT_DEPTH) } as CSSVars}>
          <article className="message-stack-item">
            <header className="message-stack-item-header">
              <AuthorPill {...new AuthorPillProps(email.sender, email.authorLabel())} />
              <small className="meta">{new Timestamp(email.sentAt).display()}</small>
            </header>
            {/* Our own agents' markup from a local database, so rendered as-is. */}
            <div className="message-stack-item-body" dangerouslySetInnerHTML={{ __html: email.bodyHtml }} />
          </article>
          {depth === 0 && slotAfterNewest}
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

// CSSProperties doesn't know about custom properties; this is the narrowest way to hand one in.
type CSSVars = CSSProperties & Record<'--depth', number>
