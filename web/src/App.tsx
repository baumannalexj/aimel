import { useCallback, useEffect, useMemo, useState } from 'react'
import { ErrorBoundary } from './app/errors/ErrorBoundary'
import { ErrorSeverity } from './app/errors/ErrorSeverity'
import { ErrorSurface, useErrorReporter } from './app/errors/ErrorSurface'
import { Footer } from './app/Footer'
import { Header } from './app/Header'
import { Layout } from './app/Layout'
import { Root } from './app/Root'
import { HistoryMode, Router, useNavigate, useRoute, useSessionFilter } from './app/Router'
import { EmailPane } from './components/emailpane/EmailPane'
import { SessionFilter } from './components/SessionFilter'
import { ThreadList } from './components/ThreadList'
import type { ClaudeSession } from './domain/ClaudeSession'
import { EmailState } from './domain/EmailState'
import type { EmailThread } from './domain/EmailThread'
import type { ThreadSummary } from './domain/ThreadSummary'
import { Anything, filtered, sorted } from './domain/Ordering'
import {
  ByLastActiveDescending,
  ThreadsByUpdatedDescending,
  ThreadsOfSession,
} from './domain/SessionOrdering'
import { EmailRepository } from './repository/EmailRepository'

// Display only: whose inbox this is.
const MAILBOX = 'alexander.baumann@aimel.com'

// Sorting and filtering are chosen here and passed down, so no component decides what order means
// and nothing silently inherits whatever order the api happened to send. Swapping either is a
// different constant, not a different component.
const SESSION_ORDER = new ByLastActiveDescending()
const THREAD_ORDER = new ThreadsByUpdatedDescending()

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
  const [sessionFilter, setSessionFilter] = useSessionFilter()
  const { reportError } = useErrorReporter()
  const [threads, setThreads] = useState<ThreadSummary[]>([])
  const [sessions, setSessions] = useState<ClaudeSession[]>([])
  const [open, setOpen] = useState<EmailThread | null>(null)
  const visibleThreads = useMemo(() => {
    const predicate = sessionFilter ? new ThreadsOfSession(sessionFilter) : new Anything<ThreadSummary>()
    return sorted(filtered(threads, predicate), THREAD_ORDER)
  }, [threads, sessionFilter])

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

  useEffect(() => {
    repository.listSessions().then(setSessions).catch(report)
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

  // Landing on the inbox with mail in it opens the newest thread, so the pane is never empty on a
  // cold load. Replaces rather than pushes: a pushed redirect makes back return here and bounce
  // forward again. A deep link is left alone -- an explicit request outranks a default.
  useEffect(() => {
    if (route.name !== 'inbox' || visibleThreads.length === 0) return
    navigate(threadPath(visibleThreads[0].threadUuid, sessionFilter), HistoryMode.Replace)
  }, [route, visibleThreads, sessionFilter, navigate])

  const markNewestRead = useCallback(
    (thread: EmailThread) => {
      const newest = thread.newest()
      if (!newest || newest.state !== EmailState.Unread) return
      // Never mark your own outgoing mail read. Unread is the recipient's queue, so doing that
      // silently deletes the message from the agent's `poll` before it ever sees it.
      if (newest.writtenByHuman()) return
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
      header={
        <Header
          productName="aimel"
          mailbox={MAILBOX}
          rightSlot={<UnreadSummary threads={threads} />}
        />
      }
      footer={<Footer version="v0.0.0" />}
    >
      <Layout
        sidebar={
          <>
            <h1>Inbox</h1>
            <SessionFilter
              sessions={sessions}
              selectedSessionUuid={sessionFilter}
              ordering={SESSION_ORDER}
              onChange={setSessionFilter}
            />
            <ThreadList
              threads={visibleThreads}
              selectedThreadUuid={open?.threadUuid ?? null}
              onOpen={(thread) => navigate(threadPath(thread.threadUuid, sessionFilter))}
            />
          </>
        }
        pane={<Pane route={route} thread={open} repository={repository} onReplied={onReplied} />}
      />
    </Root>
  )
}

// Opening a thread is a pathname change; the session filter lives in the query string, so it has
// to be carried along by hand or picking a filter and then a thread would silently clear it.
function threadPath(threadUuid: string, sessionFilter: string | null): string {
  return `/emailthreads/${threadUuid}${sessionFilter ? `?session=${sessionFilter}` : ''}`
}

function UnreadSummary({ threads }: { threads: ThreadSummary[] }) {
  const unread = threads.filter((thread) => thread.hasUnread()).length
  if (unread === 0) {
    return <span>{threads.length} threads · all read</span>
  }
  return (
    <span>
      {threads.length} threads · <strong>{unread} with unread</strong>
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
