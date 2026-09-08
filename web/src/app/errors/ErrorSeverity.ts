// A real `enum` isn't erasable syntax, so this is the object-literal replacement
// (same pattern as domain/EmailState.ts and domain/Actor.ts).
//
// Blocking means the failure stops the user from doing anything useful (the api is down) and
// gets a banner that stays until dismissed. Transient means the one action they just tried
// failed but the app is otherwise fine (a reply didn't send), and gets a toast that goes away
// on its own.
export const ErrorSeverity = {
  Blocking: 'blocking',
  Transient: 'transient',
} as const

export type ErrorSeverity = (typeof ErrorSeverity)[keyof typeof ErrorSeverity]
