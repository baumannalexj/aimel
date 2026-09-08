import type { ThreadListItem } from '../types/contract'

interface Props {
  thread: ThreadListItem
  onOpen?: (thread: ThreadListItem) => void
}

export function ThreadRow({ thread, onOpen }: Props) {
  return (
    <li className="thread-row">
      <button type="button" onClick={() => onOpen?.(thread)}>
        {thread.subject}
      </button>{' '}
      <small className="meta">
        <span className="chip">{thread.sessionShort}</span> · {thread.emailCount} email(s) · {thread.updatedAt}
      </small>
    </li>
  )
}
