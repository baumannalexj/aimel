// Verbatim mirror of src/adapters/resource/api_responses.py. Field names and casing must match exactly.

export interface ThreadListItemResponse {
  threadUuid: string
  subject: string
  emailCount: number
  unreadCount: number
  latestEmailUuid: string
  session: string
  sessionShort: string
  sessionColor: string
  updatedAt: string
}

export interface EmailItemResponse {
  emailUuid: string
  threadUuid: string
  author: string
  state: string
  sentAt: string
  sender: string
  recipient: string
  bodyHtml: string
  preview: string
}

export interface ThreadDetailResponse {
  threadUuid: string
  subject: string
  session: string
  sessionShort: string
  sessionColor: string
  emails: EmailItemResponse[]
}

export interface ReplyAcceptedResponse {
  emailUuid: string
  threadUuid: string
}

// Runtime guards so a 2xx with the wrong shape becomes a `Malformed` Result, not a crash deep in a
// mapper. Structural checks only, matching the interfaces above field for field.

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

export function isThreadListItemResponse(value: unknown): value is ThreadListItemResponse {
  return (
    isRecord(value) &&
    typeof value.threadUuid === 'string' &&
    typeof value.subject === 'string' &&
    typeof value.emailCount === 'number' &&
    typeof value.unreadCount === 'number' &&
    typeof value.latestEmailUuid === 'string' &&
    typeof value.session === 'string' &&
    typeof value.sessionShort === 'string' &&
    typeof value.sessionColor === 'string' &&
    typeof value.updatedAt === 'string'
  )
}

export function isThreadListItemResponseArray(value: unknown): value is ThreadListItemResponse[] {
  return Array.isArray(value) && value.every(isThreadListItemResponse)
}

export function isEmailItemResponse(value: unknown): value is EmailItemResponse {
  return (
    isRecord(value) &&
    typeof value.emailUuid === 'string' &&
    typeof value.threadUuid === 'string' &&
    typeof value.author === 'string' &&
    typeof value.state === 'string' &&
    typeof value.sentAt === 'string' &&
    typeof value.sender === 'string' &&
    typeof value.recipient === 'string' &&
    typeof value.bodyHtml === 'string' &&
    typeof value.preview === 'string'
  )
}

export function isThreadDetailResponse(value: unknown): value is ThreadDetailResponse {
  return (
    isRecord(value) &&
    typeof value.threadUuid === 'string' &&
    typeof value.subject === 'string' &&
    typeof value.session === 'string' &&
    typeof value.sessionShort === 'string' &&
    typeof value.sessionColor === 'string' &&
    Array.isArray(value.emails) &&
    value.emails.every(isEmailItemResponse)
  )
}

export function isReplyAcceptedResponse(value: unknown): value is ReplyAcceptedResponse {
  return isRecord(value) && typeof value.emailUuid === 'string' && typeof value.threadUuid === 'string'
}
