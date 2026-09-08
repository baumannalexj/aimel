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
