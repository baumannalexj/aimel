// Values are the wire values the python api sends, so parsing is a lookup rather than a mapping.
export enum EmailState {
  Unread = 'unread',
  Read = 'read',
  Deleted = 'deleted',
}

export function parseEmailState(value: string): EmailState {
  if (isEmailState(value)) return value
  throw new Error(`unexpected email state from api: "${value}"`)
}

function isEmailState(value: string): value is EmailState {
  return Object.values<string>(EmailState).includes(value)
}
