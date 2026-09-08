import type { ReactNode } from 'react'

export interface HeaderProps {
  productName: string
  rightSlot?: ReactNode
}

export function Header({ productName, rightSlot }: HeaderProps) {
  return (
    <header className="app-header">
      <h1>{productName}</h1>
      {rightSlot ? <div className="app-header-right">{rightSlot}</div> : null}
    </header>
  )
}
