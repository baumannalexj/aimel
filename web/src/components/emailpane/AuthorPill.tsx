// SEAM — props are settled, body is not. Ticket UI-3c.

import type { ReactElement } from 'react'
import { participantColor } from '../../domain/ParticipantColor'

export class AuthorPillProps {
  emailAddress: string
  label: string

  constructor(emailAddress: string, label: string) {
    this.emailAddress = emailAddress
    this.label = label
  }
}

function hexToRgb(hex: string): [number, number, number] {
  const normalized = hex.replace('#', '')
  return [
    parseInt(normalized.slice(0, 2), 16),
    parseInt(normalized.slice(2, 4), 16),
    parseInt(normalized.slice(4, 6), 16)
  ]
}

// WCAG relative luminance (https://www.w3.org/TR/WCAG21/#dfn-relative-luminance).
function relativeLuminance(hex: string): number {
  const [r, g, b] = hexToRgb(hex).map((channel) => {
    const s = channel / 255
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4)
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

// Whichever of black/white clears more contrast against the background wins — the
// background is an arbitrary per-participant hash, so neither is safe to assume.
function legibleForeground(backgroundHex: string): string {
  const luminance = relativeLuminance(backgroundHex)
  const contrastWithWhite = 1.05 / (luminance + 0.05)
  const contrastWithBlack = (luminance + 0.05) / 0.05
  return contrastWithWhite >= contrastWithBlack ? '#ffffff' : '#000000'
}

export function AuthorPill(props: AuthorPillProps): ReactElement {
  const background = participantColor(props.emailAddress)
  const color = legibleForeground(background)

  return (
    <span className="chip" style={{ background, color }}>
      {props.label}
    </span>
  )
}
