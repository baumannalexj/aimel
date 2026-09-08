// SEAM — props are settled, body is not. Ticket UI-3d.

import type { ReactElement } from 'react'

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

export function ReplyBox(_props: ReplyBoxProps): ReactElement {
  throw new Error('ReplyBox is not implemented yet')
}
