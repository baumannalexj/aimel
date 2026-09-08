import type { CSSProperties, ReactElement, ReactNode } from 'react'

export interface CardProps {
  accentColor?: string
  children: ReactNode
}

export function Card({ accentColor, children }: CardProps): ReactElement {
  // The accent is per-participant data, so it comes through as a custom property rather than a
  // class. Everything else about the card is in components.css.
  const accent = { '--card-accent': accentColor } as CSSProperties

  return (
    <div className={accentColor ? 'card card-accented' : 'card'} style={accentColor ? accent : undefined}>
      {children}
    </div>
  )
}
