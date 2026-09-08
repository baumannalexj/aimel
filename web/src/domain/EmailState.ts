// A real `enum` isn't erasable syntax, so this is the object-literal replacement.
export const EmailState = {
  Unread: 'unread',
  Read: 'read',
  Deleted: 'deleted',
} as const

export type EmailState = (typeof EmailState)[keyof typeof EmailState]

export function parseEmailState(value: string): EmailState {
  switch (value) {
    case EmailState.Unread:
      return EmailState.Unread
    case EmailState.Read:
      return EmailState.Read
    case EmailState.Deleted:
      return EmailState.Deleted
    default:
      throw new Error(`unexpected email state from api: "${value}"`)
  }
}
