import { useState, type ReactElement } from 'react'
import { KeyCommands, type KeyChord } from '../KeyCommands'

export class ReplyBoxProps {
  open: boolean
  onCancel: () => void
  /** Resolves when the reply has been accepted; the pane reloads the thread. */
  onSend: (body: string) => Promise<void>
  /** Which chords send. The caller picks them; only the draft's owner can act on them. */
  sendChords: KeyChord[]
  hint: string

  constructor(
    open: boolean,
    onCancel: () => void,
    onSend: (body: string) => Promise<void>,
    sendChords: KeyChord[],
    hint: string,
  ) {
    this.open = open
    this.onCancel = onCancel
    this.onSend = onSend
    this.sendChords = sendChords
    this.hint = hint
  }
}

export function ReplyBox(props: ReplyBoxProps): ReactElement | null {
  const [body, setBody] = useState('')
  const [sending, setSending] = useState(false)

  if (!props.open) return null

  const isBlank = body.trim().length === 0

  const send = async () => {
    if (isBlank || sending) return
    setSending(true)
    try {
      await props.onSend(body)
      // Only on success. Losing what someone typed to a failed send is the worst thing this
      // component can do, so the clear stays out of the finally.
      setBody('')
    } finally {
      setSending(false)
    }
  }

  const commands = new KeyCommands(props.sendChords.map((chord) => chord.boundTo(send)))

  return (
    <div className="reply-box">
      <textarea
        className="reply-box-textarea"
        value={body}
        onChange={(event) => setBody(event.target.value)}
        onKeyDown={(event) => commands.handle(event)}
        disabled={sending}
        placeholder="Write a reply…"
        autoFocus
      />
      <div className="reply-box-actions">
        <small className="meta reply-box-hint">{props.hint}</small>
        <button type="button" className="secondary-button" onClick={props.onCancel} disabled={sending}>
          Cancel
        </button>
        <button type="button" className="primary-button" onClick={send} disabled={sending || isBlank}>
          {sending ? 'Sending…' : 'Send'}
        </button>
      </div>
    </div>
  )
}
