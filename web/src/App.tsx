import { useEffect, useState } from 'react'
import { Footer } from './app/Footer'
import { Header } from './app/Header'
import { Root } from './app/Root'
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

  const rightSlot = <span>{threads.length} thread{threads.length === 1 ? '' : 's'}</span>

  return (
    <Root
      header={<Header productName="aimel" rightSlot={rightSlot} />}
      footer={<Footer version="v0.0.0" />}
    >
      {error ? (
        <p role="alert" className="notice">{error}</p>
      ) : open ? (
        <Thread thread={open} onBack={() => setOpen(null)} />
      ) : (
        <>
          <h1>Inbox</h1>
          <ThreadList threads={threads} onOpen={openThread} />
        </>
      )}
    </Root>
  )
}
