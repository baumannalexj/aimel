import type { ThreadListItemResponse } from '../api/responses'
import { hashToHex } from './ParticipantColor'

export class ThreadSummary {
  threadUuid: string
  subject: string
  session: string
  sessionShort: string
  sessionColor: string
  emailCount: number
  unreadCount: number
  latestEmailUuid: string
  updatedAt: string

  constructor(
    threadUuid: string,
    subject: string,
    session: string,
    sessionShort: string,
    sessionColor: string,
    emailCount: number,
    unreadCount: number,
    latestEmailUuid: string,
    updatedAt: string,
  ) {
    this.threadUuid = threadUuid
    this.subject = subject
    this.session = session
    this.sessionShort = sessionShort
    this.sessionColor = sessionColor
    this.emailCount = emailCount
    this.unreadCount = unreadCount
    this.latestEmailUuid = latestEmailUuid
    this.updatedAt = updatedAt
  }

  static fromResponse(response: ThreadListItemResponse): ThreadSummary {
    return new ThreadSummary(
      response.threadUuid,
      response.subject,
      response.session,
      response.sessionShort,
      response.sessionColor,
      response.emailCount,
      response.unreadCount,
      response.latestEmailUuid,
      response.updatedAt,
    )
  }

  hasUnread(): boolean {
    return this.unreadCount > 0
  }

  color(): string {
    return hashToHex(this.session)
  }
}
