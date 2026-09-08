import type { ThreadListItem } from '../types/contract'

interface Props {
  thread: ThreadListItem
  selected: boolean
  onOpen?: (thread: ThreadListItem) => void
}

export function ThreadRow({ thread, selected, onOpen }: Props) {
  const unread = thread.unreadCount > 0
  return (
    <li className={selected ? 'thread-row thread-row-selected' : 'thread-row'}>
      <button type="button" aria-current={selected} onClick={() => onOpen?.(thread)}>
        {unread ? <strong>{thread.subject}</strong> : thread.subject}
      </button>{' '}
      {unread && (
        <span className="chip" style={{ background: 'var(--color-accent-muted)' }}>
          {thread.unreadCount}
        </span>
      )}{' '}
      <small className="meta">
        <span className="chip" style={{ background: thread.sessionColor }}>{thread.sessionShort}</span> · {thread.emailCount} email(s) · {thread.updatedAt}
      </small>
    </li>
  )
}
