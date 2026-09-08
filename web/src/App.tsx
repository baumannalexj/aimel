import { useEffect, useState } from 'react'
import { ErrorBoundary } from './app/errors/ErrorBoundary'
import { ErrorSurface } from './app/errors/ErrorSurface'
import { Footer } from './app/Footer'
import { Header } from './app/Header'
import { Layout } from './app/Layout'
import { Root } from './app/Root'
import { Router, useNavigate, useRoute } from './app/Router'
import { Thread } from './components/Thread'
import { ThreadList } from './components/ThreadList'
import { aimelClient } from './repository/aimelClient'
import type { EmailItem, ThreadDetail, ThreadListItem } from './types/contract'

// ErrorSurface must sit above ErrorBoundary: the boundary reports into the surface's context, and
// the surface is what actually renders the banner. Without it a throw blanks the page silently.
export default function App() {
  return (
    <ErrorSurface>
      <ErrorBoundary>
        <Router>
          <Inbox />
        </Router>
      </ErrorBoundary>
    </ErrorSurface>
  )
}

function Inbox() {
  const route = useRoute()
  const navigate = useNavigate()
  const [threads, setThreads] = useState<ThreadListItem[]>([])
  const [open, setOpen] = useState<ThreadDetail | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    aimelClient.threads().then(setThreads).catch((cause) => setError(String(cause)))
  }, [])

  // Drives `open` from the URL rather than from clicks, so back/forward and a cold deep link all
  // land on the right thread. Each branch bails out once `open` already satisfies the route, so
  // setOpen() re-running this effect doesn't loop or re-fetch.
  useEffect(() => {
    if (route.name === 'thread') {
      if (open?.threadUuid === route.threadUuid) return
      const target = threads.find((thread) => thread.threadUuid === route.threadUuid)
      if (!target) return // threads haven't loaded yet; this effect reruns once they do
      aimelClient.thread(target.latestEmailUuid).then(setOpen).catch((cause) => setError(String(cause)))
    } else if (route.name === 'email') {
      if (open?.emails.some((email) => email.emailUuid === route.emailUuid)) return
      aimelClient.thread(route.emailUuid).then(setOpen).catch((cause) => setError(String(cause)))
    } else {
      setOpen(null)
    }
  }, [route, threads, open])

  function markRead(email: EmailItem) {
    // Only unread mail needs the round trip, and the sidebar count follows it.
    if (email.state !== 'unread') return
    aimelClient
      .markRead(email.emailUuid)
      .then(() => aimelClient.threads())
      .then(setThreads)
      .catch((cause) => setError(String(cause)))
  }

  function reload(emailUuid: string) {
    aimelClient
      .thread(emailUuid)
      .then(setOpen)
      .catch((cause) => setError(String(cause)))
  }

  function openThread(thread: ThreadListItem) {
    setError('')
    navigate(`/emailthreads/${thread.threadUuid}`)
  }

  const rightSlot = <span>{threads.length} thread{threads.length === 1 ? '' : 's'}</span>

  return (
    <Root
      header={<Header productName="aimel" rightSlot={rightSlot} />}
      footer={<Footer version="v0.0.0" />}
    >
      {error ? (
        <p role="alert" className="notice">{error}</p>
      ) : route.name === 'not-found' ? (
        <p className="notice">No page at "{route.path}".</p>
      ) : (
        <Layout
          sidebar={
            <>
              <h1>Inbox</h1>
              <ThreadList
                threads={threads}
                selectedThreadUuid={open?.threadUuid ?? null}
                onOpen={openThread}
              />
            </>
          }
          pane={
            open ? (
              <Thread
                thread={open}
                onBack={() => navigate('/inbox')}
                onReplied={(emailUuid) => reload(emailUuid)}
                onEmailOpened={markRead}
              />
            ) : (
              <p className="notice">Pick a thread to read it.</p>
            )
          }
        />
      )}
    </Root>
  )
}
