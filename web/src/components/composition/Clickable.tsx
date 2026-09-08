// Composition, not inheritance. A component that should be clickable wraps its children in
// <Clickable>; a component that should look like a card wraps them in <Card>. ThreadRow is both,
// by nesting, not by extending anything.
//
// The whole container is the hit target, not a button inside it, so keyboard and screen-reader
// behaviour has to be built by hand to match a button: role, tabIndex, Enter and Space.

import type { KeyboardEvent, ReactElement, ReactNode } from 'react'

export interface ClickableProps {
  onClick: () => void
  label: string
  selected?: boolean
  children: ReactNode
}

export function Clickable({ onClick, label, selected, children }: ClickableProps): ReactElement {
  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key !== 'Enter' && event.key !== ' ') return
    event.preventDefault()
    onClick()
  }

  // Hover and selection are CSS, keyed off aria-current, so there is no hover state in React and
  // the accessible attribute is also the styling hook -- they cannot disagree.
  return (
    <div
      className="clickable"
      role="button"
      tabIndex={0}
      aria-label={label}
      aria-current={selected}
      onClick={onClick}
      onKeyDown={handleKeyDown}
    >
      {children}
    </div>
  )
}
