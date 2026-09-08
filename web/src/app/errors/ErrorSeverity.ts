// Blocking means the failure stops the user from doing anything useful (the api is down) and
// gets a banner that stays until dismissed. Transient means the one action they just tried
// failed but the app is otherwise fine (a reply didn't send), and gets a toast that self-clears.
export enum ErrorSeverity {
  Blocking = 'blocking',
  Transient = 'transient',
}
