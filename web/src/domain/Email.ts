import type { EmailItemResponse } from '../api/responses'
import { Actor, parseActor } from './Actor'
import { EmailState, parseEmailState } from './EmailState'

export class Email {
  id: string
  actor: Actor
  state: EmailState
  sentAt: string
  sender: string
  recipient: string
  bodyHtml: string
  preview: string

  constructor(
    id: string,
    actor: Actor,
    state: EmailState,
    sentAt: string,
    sender: string,
    recipient: string,
    bodyHtml: string,
    preview: string,
  ) {
    this.id = id
    this.actor = actor
    this.state = state
    this.sentAt = sentAt
    this.sender = sender
    this.recipient = recipient
    this.bodyHtml = bodyHtml
    this.preview = preview
  }

  static fromResponse(response: EmailItemResponse): Email {
    return new Email(
      response.emailUuid,
      parseActor(response.author),
      parseEmailState(response.state),
      response.sentAt,
      response.sender,
      response.recipient,
      response.bodyHtml,
      response.preview,
    )
  }

  isUnread(): boolean {
    return this.state === EmailState.Unread
  }

  isDeleted(): boolean {
    return this.state === EmailState.Deleted
  }

  writtenByHuman(): boolean {
    return this.actor === Actor.Human
  }

  authorLabel(): string {
    return this.writtenByHuman() ? 'You' : 'AI agent'
  }
}
