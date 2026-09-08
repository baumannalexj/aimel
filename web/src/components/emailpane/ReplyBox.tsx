// SEAM — props are settled, body is not. Ticket UI-3d.

import { useState, type ReactElement } from 'react'

export class ReplyBoxProps {
  open: boolean
  onCancel: () => void
  /** Resolves when the reply has been accepted; the pane reloads the thread. */
  onSend: (body: string) => Promise<void>

  constructor(open: boolean, onCancel: () => void, onSend: (body: string) => Promise<void>) {
    this.open = open
    this.onCancel = onCancel
    this.onSend = onSend
  }
}

export function ReplyBox(props: ReplyBoxProps): ReactElement | null {
  const [body, setBody] = useState('')
  const [sending, setSending] = useState(false)

  if (!props.open) return null

  const isBlank = body.trim().length === 0

  const send = async () => {
    setSending(true)
    try {
      await props.onSend(body)
      setBody('')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="reply-box">
      <textarea
        className="reply-box-textarea"
        value={body}
        onChange={(e) => setBody(e.target.value)}
        disabled={sending}
        placeholder="Write a reply…"
      />
      <div className="reply-box-actions">
        <button type="button" className="secondary-button" onClick={props.onCancel} disabled={sending}>
          Cancel
        </button>
        <button type="button" className="primary-button" onClick={send} disabled={sending || isBlank}>
          Send
        </button>
      </div>
    </div>
  )
}
