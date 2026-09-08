// What the client returns instead of throwing. The repository switches on `kind`; the compiler
// makes that exhaustive, so a new failure mode can't silently fall through.

interface ResponseErrorBase {
  status: number
  path: string
  message: string
}

export interface Unreachable extends ResponseErrorBase {
  kind: 'unreachable'
}

export interface NotFound extends ResponseErrorBase {
  kind: 'notFound'
}

export interface Conflict extends ResponseErrorBase {
  kind: 'conflict'
}

export interface Invalid extends ResponseErrorBase {
  kind: 'invalid'
}

export interface ServerFault extends ResponseErrorBase {
  kind: 'serverFault'
}

export interface Malformed extends ResponseErrorBase {
  kind: 'malformed'
}

export type ResponseError = Unreachable | NotFound | Conflict | Invalid | ServerFault | Malformed

export function unreachable(path: string, message: string): Unreachable {
  return { kind: 'unreachable', status: 0, path, message }
}

export function notFound(path: string, status: number, message: string): NotFound {
  return { kind: 'notFound', status, path, message }
}

export function conflict(path: string, status: number, message: string): Conflict {
  return { kind: 'conflict', status, path, message }
}

export function invalid(path: string, status: number, message: string): Invalid {
  return { kind: 'invalid', status, path, message }
}

export function serverFault(path: string, status: number, message: string): ServerFault {
  return { kind: 'serverFault', status, path, message }
}

export function malformed(path: string, status: number, message: string): Malformed {
  return { kind: 'malformed', status, path, message }
}
