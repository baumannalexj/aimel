// The only place that calls fetch. One method per endpoint, returning the server's shape verbatim.

import type {
  EmailItemResponse,
  ReplyAcceptedResponse,
  ThreadDetailResponse,
  ThreadListItemResponse,
} from './responses'

export class AimelError extends Error {
  status: number
  path: string

  constructor(message: string, status: number, path: string) {
    super(message)
    this.name = 'AimelError'
    this.status = status
    this.path = path
  }
}

async function get<T>(path: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, { headers: { Accept: 'application/json' } })
  } catch (cause) {
    // A refused connection usually means the api is not running, which is worth saying plainly.
    throw new AimelError(`cannot reach the api (${String(cause)})`, 0, path)
  }
  if (!response.ok) {
    throw new AimelError(`api said ${response.status}`, response.status, path)
  }
  return (await response.json()) as T
}

async function post<T>(path: string, body: unknown): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(body),
    })
  } catch (cause) {
    // A refused connection usually means the api is not running, which is worth saying plainly.
    throw new AimelError(`cannot reach the api (${String(cause)})`, 0, path)
  }
  if (!response.ok) {
    // The api's error bodies carry a human-readable {"error": ...}, worth surfacing over a bare status.
    const message = await response
      .json()
      .then((body: { error?: string }) => body.error ?? `api said ${response.status}`)
      .catch(() => `api said ${response.status}`)
    throw new AimelError(message, response.status, path)
  }
  return (await response.json()) as T
}

export const aimelServerClient = {
  threads: () => get<ThreadListItemResponse[]>('/api/threads'),
  thread: (emailUuid: string) => get<ThreadDetailResponse>(`/api/emails/${emailUuid}/thread`),
  reply: (emailUuid: string, html: string) =>
    post<ReplyAcceptedResponse>(`/api/emails/${emailUuid}/replies`, { html }),
  markRead: (emailUuid: string) => post<EmailItemResponse>(`/api/emails/${emailUuid}/read`, {}),
}
