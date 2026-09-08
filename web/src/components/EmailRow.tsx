import type { EmailItem } from '../types/contract'

interface Props {
  email: EmailItem
  selected: boolean
  onOpen: (email: EmailItem) => void
}

export function EmailRow({ email, selected, onOpen }: Props) {
  return (
    <li>
      <button type="button" aria-current={selected} onClick={() => onOpen(email)}>
        {email.author === 'human' ? 'you' : 'agent'} · {email.preview || '(no preview)'}
      </button>{' '}
      <small>
        {email.sentAt} · {email.state}
      </small>
    </li>
  )
}
