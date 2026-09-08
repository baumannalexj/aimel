import type { ThreadListItem } from '../types/contract'
import { Card } from './composition/Card'
import { Clickable } from './composition/Clickable'

interface Props {
  thread: ThreadListItem
  selected: boolean
  onOpen?: (thread: ThreadListItem) => void
}

function accessibleLabel(thread: ThreadListItem): string {
  const unreadPart = thread.unreadCount > 0 ? `, ${thread.unreadCount} unread` : ''
  return `${thread.subject}${unreadPart}, session ${thread.sessionShort}, ${thread.emailCount} email(s), updated ${thread.updatedAt}`
}

export function ThreadRow({ thread, selected, onOpen }: Props) {
  const unread = thread.unreadCount > 0
  return (
    <li>
      <Clickable onClick={() => onOpen?.(thread)} label={accessibleLabel(thread)} selected={selected}>
        <Card>
          {unread ? <strong>{thread.subject}</strong> : thread.subject}
          {unread && (
            <span className="chip" style={{ background: 'var(--color-accent-muted)' }}>
              {thread.unreadCount}
            </span>
          )}
          <small className="meta">
            <span className="chip" style={{ background: thread.sessionColor }}>{thread.sessionShort}</span> · {thread.emailCount} email(s) · {thread.updatedAt}
          </small>
        </Card>
      </Clickable>
    </li>
  )
}
