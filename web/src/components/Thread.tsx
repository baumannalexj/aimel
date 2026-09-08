import { useEffect, useState } from 'react'
import type { EmailItem, ThreadDetail } from '../types/contract'
import { EmailDetail } from './EmailDetail'
import { EmailRow } from './EmailRow'
import { ReplyForm } from './ReplyForm'

interface Props {
  thread: ThreadDetail
  onBack: () => void
  onReplied: (newEmailUuid: string) => void
  onEmailOpened: (email: EmailItem) => void
}

export function Thread({ thread, onBack, onReplied, onEmailOpened }: Props) {
  const [openEmail, setOpenEmail] = useState<EmailItem | null>(thread.emails[0] ?? null)

  // emails are newest-first; jump straight to the latest one whenever the thread changes
  // (switching threads, or a reply landing) instead of making the user click twice.
  // Auto-selecting counts as opening it, otherwise the email you are looking at stays unread.
  useEffect(() => {
    const newest = thread.emails[0] ?? null
    setOpenEmail(newest)
    if (newest) onEmailOpened(newest)
    // onEmailOpened is deliberately not a dependency: App redefines it every render, so
    // including it would re-fire this effect forever.
  }, [thread.emails[0]?.emailUuid])

  return (
    <section>
      <button type="button" className="secondary-button" onClick={onBack}>
        &larr; all threads
      </button>
      <h2>{thread.subject}</h2>
      <small className="meta">
        <span className="chip" style={{ background: thread.sessionColor }}>{thread.sessionShort}</span> · {thread.emails.length} email(s)
      </small>

      <ul>
        {thread.emails.map((email) => (
          <EmailRow
            key={email.emailUuid}
            email={email}
            selected={openEmail?.emailUuid === email.emailUuid}
            onOpen={(picked) => {
              setOpenEmail(picked)
              onEmailOpened(picked)
            }}
          />
        ))}
      </ul>

      {openEmail ? <EmailDetail email={openEmail} /> : <p className="notice">Pick an email to read it.</p>}
      <ReplyForm emailUuid={thread.emails[0].emailUuid} onReplied={onReplied} />
    </section>
  )
}
