import type { ThreadListItem } from '../types/contract'

interface Props {
  thread: ThreadListItem
  selected: boolean
  onOpen?: (thread: ThreadListItem) => void
}

export function ThreadRow({ thread, selected, onOpen }: Props) {
  return (
    <li className={selected ? 'thread-row thread-row-selected' : 'thread-row'}>
      <button type="button" aria-current={selected} onClick={() => onOpen?.(thread)}>
        {thread.subject}
      </button>{' '}
      <small className="meta">
        <span className="chip" style={{ background: thread.sessionColor }}>{thread.sessionShort}</span> · {thread.emailCount} email(s) · {thread.updatedAt}
      </small>
    </li>
  )
}
