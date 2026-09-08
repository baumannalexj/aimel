// One method per UI use case, returning domain classes. There is one implementation, so pages take
// this class directly rather than an interface.
//
// Errors go straight to the top: unwrap throws, nothing here catches, and the root container
// renders the banner. Mapping each ResponseError kind to its own DomainException is V2 -- the
// kinds and the exception classes already exist for it, they just aren't wired yet.

import { AimelServerClient } from '../api/aimelServerClient'
import type { Result } from '../api/Result'
import type { ResponseError } from '../api/ResponseError'
import { ApiCallFailed } from '../domain/ApiCallFailed'
import { ClaudeSession } from '../domain/ClaudeSession'
import { Email } from '../domain/Email'
import { EmailThread } from '../domain/EmailThread'
import { ThreadSummary } from '../domain/ThreadSummary'

function unwrap<T>(result: Result<T, ResponseError>): T {
  if (result.kind === 'ok') return result.value
  throw new ApiCallFailed(result.error.status, result.error.path, result.error.message)
}

export class EmailRepository {
  private readonly client: AimelServerClient

  constructor() {
    this.client = new AimelServerClient()
  }

  async listInbox(): Promise<ThreadSummary[]> {
    const threads = unwrap(await this.client.threads())
    return threads.map(ThreadSummary.fromResponse)
  }

  async openThread(emailUuid: string): Promise<EmailThread> {
    return EmailThread.fromResponse(unwrap(await this.client.thread(emailUuid)))
  }

  async replyTo(emailUuid: string, body: string): Promise<EmailThread> {
    // Reloaded through the reply's own uuid, not the one replied to, so the caller sees its
    // reply even if the api ever moves a reply onto a different thread.
    const accepted = unwrap(await this.client.reply(emailUuid, body))
    return this.openThread(accepted.emailUuid)
  }

  async markRead(emailUuid: string): Promise<Email> {
    return Email.fromResponse(unwrap(await this.client.markRead(emailUuid)))
  }

  async listSessions(): Promise<ClaudeSession[]> {
    const sessions = unwrap(await this.client.sessions())
    return sessions.map(ClaudeSession.fromResponse)
  }
}
