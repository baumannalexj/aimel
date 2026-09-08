import type { ThreadListItem } from '../types/contract'
import { ThreadRow } from './ThreadRow'

interface Props {
  threads: ThreadListItem[]
  onOpen?: (thread: ThreadListItem) => void
}

export function ThreadList({ threads, onOpen }: Props) {
  if (threads.length === 0) return <p className="notice">No mail yet.</p>
  return (
    <ul>
      {threads.map((thread) => (
        <ThreadRow key={thread.threadUuid} thread={thread} onOpen={onOpen} />
      ))}
    </ul>
  )
}
