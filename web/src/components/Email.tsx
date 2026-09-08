import type { EmailItem } from '../types/contract'

interface Props {
  email: EmailItem
}

export function Email({ email }: Props) {
  return (
    <article>
      <small>
        {email.author === 'human' ? 'you' : 'agent'} · {email.sentAt} · {email.sender} &rarr;{' '}
        {email.recipient} · {email.state}
      </small>
      {/* Our own agents' markup, stored locally, so it is rendered as-is. */}
      <div dangerouslySetInnerHTML={{ __html: email.bodyHtml }} />
    </article>
  )
}
