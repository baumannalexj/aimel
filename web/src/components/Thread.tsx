import type { ThreadDetail } from '../types/contract'
import { Email } from './Email'

interface Props {
  thread: ThreadDetail
  onBack: () => void
}

export function Thread({ thread, onBack }: Props) {
  return (
    <section>
      <button type="button" onClick={onBack}>
        &larr; all threads
      </button>
      <h2>{thread.subject}</h2>
      <small>
        {thread.sessionShort} · {thread.emails.length} email(s)
      </small>
      {thread.emails.map((email) => (
        <Email key={email.emailUuid} email={email} />
      ))}
    </section>
  )
}
