// One place that talks to the api, so error handling lives here instead of in every component.

import type { ThreadListItem } from '../types/contract'

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

export const aimelClient = {
  threads: () => get<ThreadListItem[]>('/api/threads'),
}
