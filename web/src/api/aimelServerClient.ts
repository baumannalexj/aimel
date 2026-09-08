// The only place that calls fetch. One method per endpoint, returning a Result rather than
// throwing -- the repository above switches on ResponseError.kind, and the compiler holds it to
// exhaustiveness. See web/ARCHITECTURE.md, "Errors".

import {
  isEmailItemResponse,
  isReplyAcceptedResponse,
  isSessionListItemResponseArray,
  isThreadDetailResponse,
  isThreadListItemResponseArray,
} from './responses'
import type {
  EmailItemResponse,
  ReplyAcceptedResponse,
  SessionListItemResponse,
  ThreadDetailResponse,
  ThreadListItemResponse,
} from './responses'
import { err, ok } from './Result'
import type { Result } from './Result'
import { conflict, invalid, malformed, notFound, serverFault, unreachable } from './ResponseError'
import type { ResponseError } from './ResponseError'

function toResponseError(status: number, path: string, message: string): ResponseError {
  if (status === 404) return notFound(path, status, message)
  if (status === 409) return conflict(path, status, message)
  if (status === 422) return invalid(path, status, message)
  return serverFault(path, status, message)
}

function logged(error: ResponseError): ResponseError {
  console.error(`aimelServerClient: ${error.kind} (${error.status}) at ${error.path}: ${error.message}`)
  return error
}

async function request<T>(
  path: string,
  init: RequestInit | undefined,
  isExpectedShape: (value: unknown) => value is T,
): Promise<Result<T, ResponseError>> {
  let response: Response
  try {
    response = await fetch(path, init)
  } catch (cause) {
    // A refused connection usually means the api is not running, which is worth saying plainly.
    return err(logged(unreachable(path, `cannot reach the api (${String(cause)})`)))
  }

  if (!response.ok) {
    // The api's error bodies carry a human-readable {"error": ...}, worth surfacing over a bare status.
    const message = await response
      .json()
      .then((body: { error?: string }) => body.error ?? `api said ${response.status}`)
      .catch(() => `api said ${response.status}`)
    return err(logged(toResponseError(response.status, path, message)))
  }

  let body: unknown
  try {
    body = await response.json()
  } catch (cause) {
    return err(logged(malformed(path, response.status, `response body was not valid json (${String(cause)})`)))
  }

  if (!isExpectedShape(body)) {
    return err(logged(malformed(path, response.status, 'response body did not match the expected shape')))
  }

  return ok(body)
}

function requestJson<T>(
  path: string,
  method: string,
  requestBody: unknown,
  isExpectedShape: (value: unknown) => value is T,
): Promise<Result<T, ResponseError>> {
  return request(
    path,
    {
      method,
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(requestBody),
    },
    isExpectedShape,
  )
}

/** Constructed by EmailRepository. Nothing in the UI tiers should reach it directly. */
export class AimelServerClient {
  threads(): Promise<Result<ThreadListItemResponse[], ResponseError>> {
    return request('/api/threads', { headers: { Accept: 'application/json' } }, isThreadListItemResponseArray)
  }

  thread(emailUuid: string): Promise<Result<ThreadDetailResponse, ResponseError>> {
    return request(
      `/api/emails/${emailUuid}/thread`,
      { headers: { Accept: 'application/json' } },
      isThreadDetailResponse,
    )
  }

  reply(emailUuid: string, html: string): Promise<Result<ReplyAcceptedResponse, ResponseError>> {
    return requestJson(`/api/emails/${emailUuid}/replies`, 'POST', { html }, isReplyAcceptedResponse)
  }

  markRead(emailUuid: string): Promise<Result<EmailItemResponse, ResponseError>> {
    return requestJson(`/api/emails/${emailUuid}/read`, 'POST', {}, isEmailItemResponse)
  }

  sessions(): Promise<Result<SessionListItemResponse[], ResponseError>> {
    return request('/api/sessions', { headers: { Accept: 'application/json' } }, isSessionListItemResponseArray)
  }
}
