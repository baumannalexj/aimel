import { useCallback, useEffect, useMemo, useState } from 'react'
import { ErrorBoundary } from './app/errors/ErrorBoundary'
import { ErrorSeverity } from './app/errors/ErrorSeverity'
import { ErrorSurface, useErrorReporter } from './app/errors/ErrorSurface'
import { Footer } from './app/Footer'
import { Header } from './app/Header'
import { Layout } from './app/Layout'
import { Root } from './app/Root'
import { Router, useNavigate, useRoute } from './app/Router'
import { EmailPane } from './components/emailpane/EmailPane'
import { ThreadList } from './components/ThreadList'
import { EmailState } from './domain/EmailState'
import type { EmailThread } from './domain/EmailThread'
import type { ThreadSummary } from './domain/ThreadSummary'
import { EmailRepository } from './repository/EmailRepository'

// ErrorSurface must sit above ErrorBoundary: the boundary reports into the surface's context, and
// the surface is what actually renders the banner. Without it a throw blanks the page silently.
export default function App() {
  const repository = useMemo(() => new EmailRepository(), [])

  return (
    <ErrorSurface>
      <ErrorBoundary>
        <Router>
          <Inbox repository={repository} />
        </Router>
      </ErrorBoundary>
    </ErrorSurface>
  )
}

interface InboxProps {
  repository: EmailRepository
}

function Inbox({ repository }: InboxProps) {
  const route = useRoute()
  const navigate = useNavigate()
  const { reportError } = useErrorReporter()
  const [threads, setThreads] = useState<ThreadSummary[]>([])
  const [open, setOpen] = useState<EmailThread | null>(null)

  // Async rejections never reach an ErrorBoundary -- React only catches throws during render -- so
  // every await here has to hand the failure to the surface itself or it vanishes into the console.
  const report = useCallback(
    (thrown: unknown) => {
      reportError({
        message: thrown instanceof Error ? thrown.message : String(thrown),
        severity: ErrorSeverity.Blocking,
        cause: thrown,
      })
    },
    [reportError],
  )

  useEffect(() => {
    repository.listInbox().then(setThreads).catch(report)
  }, [repository, report])

  // Drives `open` from the URL rather than from clicks, so back/forward and a cold deep link all
  // land on the right thread. Each branch bails out once `open` already satisfies the route, so
  // setOpen() re-running this effect doesn't loop or re-fetch.
  useEffect(() => {
    if (route.name === 'thread') {
      if (open?.threadUuid === route.threadUuid) return
      const target = threads.find((thread) => thread.threadUuid === route.threadUuid)
      if (!target) return // threads haven't loaded yet; this effect reruns once they do
      repository.openThread(target.latestEmailUuid).then(setOpen).catch(report)
      return
    }
    if (route.name === 'email') {
      if (open?.emails.some((email) => email.emailUuid === route.emailUuid)) return
      repository.openThread(route.emailUuid).then(setOpen).catch(report)
      return
    }
    setOpen(null)
  }, [route, threads, open, repository, report])

  const markNewestRead = useCallback(
    (thread: EmailThread) => {
      const newest = thread.newest()
      if (!newest || newest.state !== EmailState.Unread) return
      repository
        .markRead(newest.emailUuid)
        .then(() => repository.listInbox())
        .then(setThreads)
        .catch(report)
    },
    [repository, report],
  )

  // Opening a thread is what marks its newest email read, so the sidebar count follows the URL.
  useEffect(() => {
    if (open) markNewestRead(open)
  }, [open, markNewestRead])

  const onReplied = (thread: EmailThread) => {
    setOpen(thread)
    repository.listInbox().then(setThreads).catch(report)
  }

  return (
    <Root
      header={<Header productName="aimel" rightSlot={<ThreadCount count={threads.length} />} />}
      footer={<Footer version="v0.0.0" />}
    >
      <Layout
        sidebar={
          <>
            <h1>Inbox</h1>
            <ThreadList
              threads={threads}
              selectedThreadUuid={open?.threadUuid ?? null}
              onOpen={(thread) => navigate(`/emailthreads/${thread.threadUuid}`)}
            />
          </>
        }
        pane={<Pane route={route} thread={open} repository={repository} onReplied={onReplied} />}
      />
    </Root>
  )
}

function ThreadCount({ count }: { count: number }) {
  return (
    <span>
      {count} thread{count === 1 ? '' : 's'}
    </span>
  )
}

interface PaneProps {
  route: ReturnType<typeof useRoute>
  thread: EmailThread | null
  repository: EmailRepository
  onReplied: (thread: EmailThread) => void
}

function Pane({ route, thread, repository, onReplied }: PaneProps) {
  if (route.name === 'not-found') {
    return <p className="notice">No page at "{route.path}".</p>
  }
  if (!thread) {
    return <p className="notice">Pick a thread to read it.</p>
  }
  return <EmailPane thread={thread} repository={repository} onThreadReloaded={onReplied} />
}
