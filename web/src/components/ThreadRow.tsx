import { Timestamp } from '../domain/Timestamp'
import type { ThreadSummary } from '../domain/ThreadSummary'
import { AccentedCard } from './composition/Card'
import { Clickable } from './composition/Clickable'

interface Props {
  thread: ThreadSummary
  selected: boolean
  onOpen?: (thread: ThreadSummary) => void
}

function accessibleLabel(thread: ThreadSummary, updated: string): string {
  const unreadPart = thread.unreadCount > 0 ? `, ${thread.unreadCount} unread` : ''
  return `${thread.subject}${unreadPart}, session ${thread.sessionShort}, ${thread.emailCount} email(s), updated ${updated}`
}

export function ThreadRow({ thread, selected, onOpen }: Props) {
  const unread = thread.unreadCount > 0
  const updated = new Timestamp(thread.updatedAt).display()
  const sessionColor = thread.color()

  return (
    <li>
      <Clickable
        onClick={() => onOpen?.(thread)}
        label={accessibleLabel(thread, updated)}
        selected={selected}
      >
        <AccentedCard accentColor={sessionColor}>
          <div className="thread-summary">
            <div className="thread-summary-title">
              <span className="thread-summary-subject">
                {unread ? <strong>{thread.subject}</strong> : thread.subject}
              </span>
              {unread && (
                <span className="chip" style={{ background: 'var(--color-accent-muted)' }}>
                  {thread.unreadCount}
                </span>
              )}
            </div>
            <small className="meta thread-summary-meta">
              <span className="chip" style={{ background: sessionColor }}>{thread.sessionShort}</span>
              <span>
                {thread.emailCount} · {updated}
              </span>
            </small>
          </div>
        </AccentedCard>
      </Clickable>
    </li>
  )
}
