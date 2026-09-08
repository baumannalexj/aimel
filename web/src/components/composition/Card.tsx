// SEAM — signature is settled, body is not. See Clickable.tsx for why these compose.

import type { ReactNode } from 'react'

export interface CardProps {
  accentColor?: string
  children: ReactNode
}

export function Card(_props: CardProps) {
  throw new Error('Card is not implemented yet')
}
