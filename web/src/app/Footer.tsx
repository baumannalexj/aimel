export interface FooterLink {
  label: string
  href: string
}

export interface FooterProps {
  version: string
  link?: FooterLink
}

export function Footer({ version, link }: FooterProps) {
  return (
    <footer className="app-footer">
      <span className="app-footer-version">{version}</span>
      {link ? <a href={link.href}>{link.label}</a> : null}
    </footer>
  )
}
