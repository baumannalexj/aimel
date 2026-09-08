import { hashToHex } from '../domain/ParticipantColor'
import { Timestamp } from '../domain/Timestamp'
import type { ThreadListItem } from '../types/contract'
import { Card } from './composition/Card'
import { Clickable } from './composition/Clickable'

interface Props {
  thread: ThreadListItem
  selected: boolean
  onOpen?: (thread: ThreadListItem) => void
}

function accessibleLabel(thread: ThreadListItem, updated: string): string {
  const unreadPart = thread.unreadCount > 0 ? `, ${thread.unreadCount} unread` : ''
  return `${thread.subject}${unreadPart}, session ${thread.sessionShort}, ${thread.emailCount} email(s), updated ${updated}`
}

export function ThreadRow({ thread, selected, onOpen }: Props) {
  const unread = thread.unreadCount > 0
  const updated = new Timestamp(thread.updatedAt).display()
  const sessionColor = hashToHex(thread.session)

  return (
    <li>
      <Clickable
        onClick={() => onOpen?.(thread)}
        label={accessibleLabel(thread, updated)}
        selected={selected}
      >
        <Card accentColor={sessionColor}>
          {unread ? <strong>{thread.subject}</strong> : thread.subject}
          {unread && (
            <span className="chip" style={{ background: 'var(--color-accent-muted)' }}>
              {thread.unreadCount}
            </span>
          )}
          <small className="meta">
            <span className="chip" style={{ background: sessionColor }}>{thread.sessionShort}</span> ·{' '}
            {thread.emailCount} email(s) · {updated}
          </small>
        </Card>
      </Clickable>
    </li>
  )
}
