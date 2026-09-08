import type { ThreadListItem } from '../types/contract'

interface Props {
  thread: ThreadListItem
  onOpen?: (thread: ThreadListItem) => void
}

export function ThreadRow({ thread, onOpen }: Props) {
  return (
    <li>
      <button type="button" onClick={() => onOpen?.(thread)}>
        {thread.subject}
      </button>{' '}
      <small>
        {thread.sessionShort} · {thread.emailCount} email(s) · {thread.updatedAt}
      </small>
    </li>
  )
}
