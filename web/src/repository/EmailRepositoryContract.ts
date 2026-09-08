/**
 * The repository seam.
 *
 * Views code against `IEmailRepository`; `EmailRepository` is the real one and
 * `NoopEmailRepository` keeps a component renderable in isolation without a running api.
 *
 * The structural view types this file used to declare are gone -- the domain classes they stood in
 * for now exist, so the interface names them directly.
 */

import type { Email } from '../domain/Email'
import type { EmailThread } from '../domain/EmailThread'
import type { ThreadSummary } from '../domain/ThreadSummary'

/** One method per UI use case, named for the use case rather than the endpoint. */
export interface IEmailRepository {
  listInbox(): Promise<ThreadSummary[]>
  openThread(emailUuid: string): Promise<EmailThread>
  /** Returns the reloaded thread, so a caller never has to re-fetch to see its own reply. */
  replyTo(emailUuid: string, body: string): Promise<EmailThread>
  markRead(emailUuid: string): Promise<Email>
}

export class NotImplementedYet extends Error {
  constructor(method: string) {
    super(`${method} is not implemented yet — the seam is a no-op`)
    this.name = 'NotImplementedYet'
  }
}

/** For rendering a component without an api behind it. */
export class NoopEmailRepository implements IEmailRepository {
  async listInbox(): Promise<ThreadSummary[]> {
    return []
  }

  async openThread(): Promise<EmailThread> {
    throw new NotImplementedYet('openThread')
  }

  async replyTo(): Promise<EmailThread> {
    throw new NotImplementedYet('replyTo')
  }

  async markRead(): Promise<Email> {
    throw new NotImplementedYet('markRead')
  }
}
