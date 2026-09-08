/**
 * The repository seam, as a no-op.
 *
 * Deliberately implementation-free so both sides can be built at once: views code against
 * `IEmailRepository`, the real implementation arrives behind it, and `NoopEmailRepository` keeps the
 * app compiling and renderable in between.
 *
 * The view types here are STRUCTURAL on purpose. The domain classes in `web/src/domain/` will satisfy
 * them, so nothing has to import a class that does not exist yet. When domain lands, these become
 * `type ThreadSummaryView = ThreadSummary` and so on, or disappear.
 */

export enum EmailStateView {
  Unread = 'unread',
  Read = 'read',
  Deleted = 'deleted',
}

export enum ActorView {
  Human = 'human',
  AiAgent = 'ai_agent',
}

export interface EmailView {
  emailUuid: string
  actor: ActorView
  state: EmailStateView
  sentAt: string
  sender: string
  recipient: string
  bodyHtml: string
  preview: string
}

export interface ThreadSummaryView {
  threadUuid: string
  subject: string
  sessionShort: string
  sessionColor: string
  emailCount: number
  unreadCount: number
  latestEmailUuid: string
  updatedAt: string
}

export interface EmailThreadView {
  threadUuid: string
  subject: string
  sessionShort: string
  sessionColor: string
  emails: EmailView[]
}

/** One method per UI use case, named for the use case rather than the endpoint. */
export interface IEmailRepository {
  listInbox(): Promise<ThreadSummaryView[]>
  openThread(emailUuid: string): Promise<EmailThreadView>
  /** Returns the reloaded thread, so a caller never has to re-fetch to see its own reply. */
  replyTo(emailUuid: string, body: string): Promise<EmailThreadView>
  markRead(emailUuid: string): Promise<EmailView>
}

export class NotImplementedYet extends Error {
  constructor(method: string) {
    super(`${method} is not implemented yet — the seam is a no-op`)
    this.name = 'NotImplementedYet'
  }
}

/** Keeps the app compiling and the views renderable while the real one is written. */
export class NoopEmailRepository implements IEmailRepository {
  async listInbox(): Promise<ThreadSummaryView[]> {
    return []
  }

  async openThread(): Promise<EmailThreadView> {
    throw new NotImplementedYet('openThread')
  }

  async replyTo(): Promise<EmailThreadView> {
    throw new NotImplementedYet('replyTo')
  }

  async markRead(): Promise<EmailView> {
    throw new NotImplementedYet('markRead')
  }
}
