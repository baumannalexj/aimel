// Composes the pane from the four seams so their owners never share a file.
// Reply state lives here rather than in ReplyBox because the trigger is in the header row and the
// box opens further down the stack -- one piece of state, two places on screen.

import { useState } from 'react'
import type { EmailThread } from '../../domain/EmailThread'
import type { EmailRepository } from '../../repository/EmailRepository'
import { MessageStack, MessageStackProps } from './MessageStack'
import { PaneHeader, PaneHeaderProps } from './PaneHeader'
import { ReplyBox, ReplyBoxProps } from './ReplyBox'

const NESTING_LIMIT = 5

interface Props {
  thread: EmailThread
  repository: EmailRepository
  onThreadReloaded: (thread: EmailThread) => void
}

export function EmailPane({ thread, repository, onThreadReloaded }: Props) {
  const [replying, setReplying] = useState(false)
  const newest = thread.newest()

  const send = async (body: string) => {
    if (!newest) return
    onThreadReloaded(await repository.replyTo(newest.emailUuid, body))
    setReplying(false)
  }

  const replyBox = (
    <ReplyBox {...new ReplyBoxProps(replying, () => setReplying(false), send)} />
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
