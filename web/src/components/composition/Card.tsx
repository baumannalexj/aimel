import type { CSSProperties, ReactElement, ReactNode } from 'react'

// Two components rather than one with an optional accent. The caller knows which kind of card it
// wants, so it says so by name instead of passing a flag and making this file branch on it.

export interface CardProps {
  children: ReactNode
}

export function Card({ children }: CardProps): ReactElement {
  return <div className="card">{children}</div>
}

export interface AccentedCardProps {
  accentColor: string
  children: ReactNode
}

export function AccentedCard({ accentColor, children }: AccentedCardProps): ReactElement {
  // The accent is per-participant data, so it rides in as a custom property. Everything else about
  // a card is in components.css.
  const accent = { '--card-accent': accentColor } as CSSProperties

  return (
    <div className="card card-accented" style={accent}>
      {children}
    </div>
  )
}
