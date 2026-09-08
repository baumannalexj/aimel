// Composes the pane from the four seams so their owners never share a file.
// Reply state lives here rather than in ReplyBox because the trigger is in the header row and the
// box opens further down the stack -- one piece of state, two places on screen.

import { useState } from 'react'
import { ErrorSeverity } from '../../app/errors/ErrorSeverity'
import { useErrorReporter } from '../../app/errors/ErrorSurface'
import type { EmailThread } from '../../domain/EmailThread'
import type { EmailRepository } from '../../repository/EmailRepository'
import { KeyChord, Modifier } from '../KeyCommands'
import { MessageStack, MessageStackProps } from './MessageStack'
import { PaneHeader, PaneHeaderProps } from './PaneHeader'
import { ReplyBox, ReplyBoxProps } from './ReplyBox'

const NESTING_LIMIT = 5

// Both, because Cmd is the mac chord and Ctrl is everywhere else, and a send shortcut that only
// works on one of them reads as broken rather than as unsupported.
const SEND_CHORDS = [
  new KeyChord('Enter', [Modifier.Meta]),
  new KeyChord('Enter', [Modifier.Ctrl]),
]
const SEND_HINT = '⌘↵ to send'

interface Props {
  thread: EmailThread
  repository: EmailRepository
  onThreadReloaded: (thread: EmailThread) => void
}

export function EmailPane({ thread, repository, onThreadReloaded }: Props) {
  const [replying, setReplying] = useState(false)
  const { reportError } = useErrorReporter()
  const newest = thread.newest()

  // A rejected promise inside an event handler never reaches an ErrorBoundary -- React only catches
  // throws during render. Without this the banner would never fire for the most likely failure there
  // is, a reply that didn't send. Rethrown so ReplyBox still knows not to clear the user's text.
  const send = async (body: string) => {
    if (!newest) return
    try {
      onThreadReloaded(await repository.replyTo(newest.emailUuid, body))
      setReplying(false)
    } catch (thrown) {
      reportError({
        message: thrown instanceof Error ? thrown.message : String(thrown),
        severity: ErrorSeverity.Blocking,
        cause: thrown,
      })
      throw thrown
    }
  }

  const replyBox = (
    <ReplyBox
      {...new ReplyBoxProps(replying, () => setReplying(false), send, SEND_CHORDS, SEND_HINT)}
    />
  )

  return (
    <section className="email-pane">
      <div className="email-pane-top">
        <PaneHeader {...new PaneHeaderProps(thread.session, thread.subject)} />
        <button type="button" className="secondary-button" onClick={() => setReplying(true)}>
          Reply
        </button>
      </div>
      <MessageStack {...new MessageStackProps(thread.emails, NESTING_LIMIT, replyBox)} />
    </section>
  )
}
