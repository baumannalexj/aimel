import { Root } from './Root'
import { Header } from './Header'
import { Footer } from './Footer'

export function RootDemo() {
  return (
    <Root
      header={<Header productName="aimel" rightSlot={<span>3 unread</span>} />}
      footer={<Footer version="v0.0.0-dev" link={{ label: 'source', href: 'https://github.com/baumannalexj/aimel' }} />}
    >
      <p>placeholder thread content</p>
    </Root>
  )
}
