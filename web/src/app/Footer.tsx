import type { ReactNode } from 'react'

export interface FooterLink {
  label: string
  href: string
}

export interface FooterProps {
  version: string
  link?: FooterLink
  /** For the database size indicator once it has an endpoint. Empty until then. */
  statusSlot?: ReactNode
}

export function Footer({ version, link, statusSlot }: FooterProps) {
  return (
    <footer className="app-footer">
      <span className="app-footer-version">{version}</span>
      {statusSlot ? <span className="app-footer-status">{statusSlot}</span> : null}
      {link ? (
        <a className="app-footer-link" href={link.href}>
          {link.label}
        </a>
      ) : null}
    </footer>
  )
}
