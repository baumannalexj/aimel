import { useEffect, useState } from 'react'
import { Thread } from './components/Thread'
import { ThreadList } from './components/ThreadList'
import { aimelClient } from './repository/aimelClient'
import type { ThreadDetail, ThreadListItem } from './types/contract'

export default function App() {
  const [threads, setThreads] = useState<ThreadListItem[]>([])
  const [open, setOpen] = useState<ThreadDetail | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    aimelClient.threads().then(setThreads).catch((cause) => setError(String(cause)))
  }, [])

  function openThread(thread: ThreadListItem) {
    setError('')
    aimelClient
      .thread(thread.latestEmailUuid)
      .then(setOpen)
      .catch((cause) => setError(String(cause)))
  }

  if (error) return <main role="alert">{error}</main>
  if (open) return <main><Thread thread={open} onBack={() => setOpen(null)} /></main>

  return (
    <main>
      <h1>Inbox</h1>
      <ThreadList threads={threads} onOpen={openThread} />
    </main>
  )
}
