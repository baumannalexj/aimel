// SEAM — signatures are settled, bodies are not.
//
// Composition, not inheritance. A component that should be clickable wraps its children in
// <Clickable>; a component that should look like a card wraps them in <Card>. ThreadRow is both,
// by nesting, not by extending anything.
//
// The point is that the whole container is the hit target, not a button inside it. Keyboard and
// screen-reader behaviour still has to match a button: role, tabIndex, Enter and Space.

import { useState, type KeyboardEvent, type ReactElement, type ReactNode } from 'react'

export interface ClickableProps {
  onClick: () => void
  label: string
  selected?: boolean
  children: ReactNode
}

export function Clickable({ onClick, label, selected, children }: ClickableProps): ReactElement {
  const [hovered, setHovered] = useState(false)

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key !== 'Enter' && event.key !== ' ') return
    event.preventDefault()
    onClick()
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={label}
      aria-current={selected}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        cursor: 'pointer',
        background: selected
          ? 'var(--color-surface-sunken)'
          : hovered
            ? 'var(--color-surface-raised)'
            : undefined,
      }}
    >
      {children}
    </div>
  )
}
