import type { EmailItem } from '../types/contract'

interface Props {
  email: EmailItem
}

export function EmailDetail({ email }: Props) {
  return (
    <article className="email">
      <small className="meta">
        {email.author === 'human' ? 'you' : 'agent'} · {email.sentAt} · {email.sender} &rarr;{' '}
        {email.recipient} · {email.state}
      </small>
      {/* Our own agents' markup from a local database, so rendered as-is. */}
      <div dangerouslySetInnerHTML={{ __html: email.bodyHtml }} />
    </article>
  )
}
