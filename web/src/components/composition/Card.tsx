// SEAM — signature is settled, body is not. See Clickable.tsx for why these compose.

import type { ReactElement, ReactNode } from 'react'

export interface CardProps {
  accentColor?: string
  children: ReactNode
}

export function Card({ accentColor, children }: CardProps): ReactElement {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'baseline',
        gap: 'var(--space-3)',
        padding: 'var(--space-3) var(--space-4)',
        borderBottom: '1px solid var(--color-border)',
        borderLeft: accentColor ? `3px solid ${accentColor}` : undefined,
      }}
    >
      {children}
    </div>
  )
}
