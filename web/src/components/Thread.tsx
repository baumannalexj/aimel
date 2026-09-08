import { useState } from 'react'
import type { EmailItem, ThreadDetail } from '../types/contract'
import { EmailDetail } from './EmailDetail'
import { EmailRow } from './EmailRow'

interface Props {
  thread: ThreadDetail
  onBack: () => void
}

export function Thread({ thread, onBack }: Props) {
  const [openEmail, setOpenEmail] = useState<EmailItem | null>(null)

  return (
    <section>
      <button type="button" onClick={onBack}>
        &larr; all threads
      </button>
      <h2>{thread.subject}</h2>
      <small>
        {thread.sessionShort} · {thread.emails.length} email(s)
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

      {openEmail ? <EmailDetail email={openEmail} /> : <p>Pick an email to read it.</p>}
    </section>
  )
}
