import type { ReactNode } from 'react'

export interface RootProps {
  header: ReactNode
  footer: ReactNode
  children: ReactNode
}

export function Root({ header, footer, children }: RootProps) {
  return (
    <div className="app-root">
      {header}
      <main className="app-main">{children}</main>
      {footer}
    </div>
  )
}
