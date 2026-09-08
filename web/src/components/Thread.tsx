import { useState } from 'react'
import type { EmailItem, ThreadDetail } from '../types/contract'
import { EmailDetail } from './EmailDetail'
import { EmailRow } from './EmailRow'
import { ReplyForm } from './ReplyForm'

interface Props {
  thread: ThreadDetail
  onBack: () => void
  onReplied: (newEmailUuid: string) => void
}

export function Thread({ thread, onBack, onReplied }: Props) {
  const [openEmail, setOpenEmail] = useState<EmailItem | null>(null)

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
            onOpen={setOpenEmail}
          />
        ))}
      </ul>

      {openEmail ? <EmailDetail email={openEmail} /> : <p className="notice">Pick an email to read it.</p>}
      <ReplyForm emailUuid={thread.emails[0].emailUuid} onReplied={onReplied} />
    </section>
  )
}
