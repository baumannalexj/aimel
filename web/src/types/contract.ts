// Mirrors the api's json contract. Kept hand-written and small; generate it later if it grows.

export interface ThreadListItem {
  threadUuid: string
  subject: string
  emailCount: number
  latestEmailUuid: string
  session: string
  sessionShort: string
  sessionColor: string
  updatedAt: string
}

export interface EmailItem {
  emailUuid: string
  author: 'human' | 'ai_agent'
  state: 'unread' | 'read' | 'deleted'
  sentAt: string
  sender: string
  recipient: string
  bodyHtml: string
  preview: string
}

export interface ThreadDetail {
  threadUuid: string
  subject: string
  session: string
  sessionShort: string
  sessionColor: string
  emails: EmailItem[]
}

export interface ReplyResult {
  emailUuid: string
  threadUuid: string
}
