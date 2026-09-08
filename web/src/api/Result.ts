export interface Ok<T> {
  kind: 'ok'
  value: T
}

export interface Err<E> {
  kind: 'err'
  error: E
}

export type Result<T, E> = Ok<T> | Err<E>

export function ok<T>(value: T): Ok<T> {
  return { kind: 'ok', value }
}

export function err<E>(error: E): Err<E> {
  return { kind: 'err', error }
}
