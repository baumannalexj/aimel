// SEAM — signatures are settled, bodies are not.
//
// Composition, not inheritance. A component that should be clickable wraps its children in
// <Clickable>; a component that should look like a card wraps them in <Card>. ThreadRow is both,
// by nesting, not by extending anything.
//
// The point is that the whole container is the hit target, not a button inside it. Keyboard and
// screen-reader behaviour still has to match a button: role, tabIndex, Enter and Space.

import type { ReactElement, ReactNode } from 'react'

export interface ClickableProps {
  onClick: () => void
  label: string
  selected?: boolean
  children: ReactNode
}

export function Clickable(_props: ClickableProps): ReactElement {
  throw new Error('Clickable is not implemented yet')
}
