import { useState } from 'react'
import { aimelClient } from '../repository/aimelClient'

interface Props {
  emailUuid: string
  onReplied: (newEmailUuid: string) => void
}

function escapeHtml(text: string) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

export function ReplyForm({ emailUuid, onReplied }: Props) {
  const [body, setBody] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')

  const trimmed = body.trim()

  function submit() {
    setSending(true)
    setError('')
    aimelClient
      .reply(emailUuid, `<p>${escapeHtml(trimmed)}</p>`)
      .then((result) => {
        setBody('')
        onReplied(result.emailUuid)
      })
      .catch((cause) => setError(String(cause)))
      .finally(() => setSending(false))
  }

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault()
        submit()
      }}
    >
      <textarea
        value={body}
        onChange={(event) => setBody(event.target.value)}
        placeholder="Write a reply…"
        disabled={sending}
      />
      <button type="submit" disabled={sending || trimmed.length === 0}>
        Reply
      </button>
      {error ? <p role="alert">{error}</p> : null}
    </form>
  )
}
