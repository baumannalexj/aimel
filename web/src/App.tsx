import { useEffect, useState } from 'react'
import { ThreadList } from './components/ThreadList'
import { aimelClient } from './repository/aimelClient'
import type { ThreadListItem } from './types/contract'

export default function App() {
  const [threads, setThreads] = useState<ThreadListItem[]>([])
  const [error, setError] = useState<string>('')

  useEffect(() => {
    aimelClient
      .threads()
      .then(setThreads)
      .catch((cause) => setError(String(cause)))
  }, [])

  return (
    <main>
      <h1>Inbox</h1>
      {error ? <p role="alert">{error}</p> : <ThreadList threads={threads} />}
    </main>
  )
}
