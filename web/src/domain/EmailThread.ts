import type { ThreadDetailResponse } from '../api/responses'
import { Email } from './Email'
import { hashToHex } from './ParticipantColor'

export class EmailThread {
  threadUuid: string
  subject: string
  session: string
  sessionShort: string
  sessionColor: string
  emails: Email[]

  constructor(
    threadUuid: string,
    subject: string,
    session: string,
    sessionShort: string,
    sessionColor: string,
    emails: Email[],
  ) {
    this.threadUuid = threadUuid
    this.subject = subject
    this.session = session
    this.sessionShort = sessionShort
    this.sessionColor = sessionColor
    this.emails = emails
  }

  static fromResponse(response: ThreadDetailResponse): EmailThread {
    return new EmailThread(
      response.threadUuid,
      response.subject,
      response.session,
      response.sessionShort,
      response.sessionColor,
      response.emails.map(Email.fromResponse),
    )
  }

  // The api sends emails newest-first.
  newest(): Email | undefined {
    return this.emails[0]
  }

  unreadCount(): number {
    return this.emails.filter((email) => email.isUnread()).length
  }

  color(): string {
    return hashToHex(this.session)
  }
}
