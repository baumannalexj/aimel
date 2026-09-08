import type { ReactNode } from 'react'

export interface LayoutProps {
  sidebar: ReactNode
  pane: ReactNode
}

export function Layout({ sidebar, pane }: LayoutProps) {
  return (
    <div className="layout">
      <aside className="layout-sidebar">{sidebar}</aside>
      <section className="layout-pane">{pane}</section>
    </div>
  )
}
