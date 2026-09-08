import type { ReactNode } from 'react'

export interface HeaderProps {
  productName: string
  /** The mailbox this is showing, so it's obvious whose inbox you're looking at. */
  mailbox: string
  rightSlot?: ReactNode
}

export function Header({ productName, mailbox, rightSlot }: HeaderProps) {
  return (
    <header className="app-header">
      <div className="app-header-brand">
        <span className="app-header-mark" aria-hidden="true" />
        <h1 className="app-header-title">{productName}</h1>
        <span className="app-header-mailbox">{mailbox}</span>
      </div>
      {rightSlot ? <div className="app-header-right">{rightSlot}</div> : null}
    </header>
  )
}
