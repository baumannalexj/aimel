import type { ThreadSummary } from '../domain/ThreadSummary'
import { ThreadRow } from './ThreadRow'

interface Props {
  threads: ThreadSummary[]
  selectedThreadUuid: string | null
  onOpen?: (thread: ThreadSummary) => void
}

export function ThreadList({ threads, selectedThreadUuid, onOpen }: Props) {
  if (threads.length === 0) return <p className="notice">No mail yet.</p>
  return (
    <ul>
      {threads.map((thread) => (
        <ThreadRow
          key={thread.threadUuid}
          thread={thread}
          selected={thread.threadUuid === selectedThreadUuid}
          onOpen={onOpen}
        />
      ))}
    </ul>
  )
}
