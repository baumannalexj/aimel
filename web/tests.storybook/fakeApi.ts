// The stub replaces `fetch`, nothing above it.
//
// Two reasons, and the second is the important one. Mocking the repository would skip the mapping
// from wire shapes to domain models, which is exactly where a renamed field or a bad enum value
// bites -- so every story is also a contract test against responses.ts. And EmailRepository
// deliberately constructs its own client with no injection point, so stubbing fetch is the only way
// to fake the api without putting a seam back into production code purely to serve tests.

import type { EmailItemResponse, ReplyAcceptedResponse, ThreadDetailResponse, ThreadListItemResponse } from '../src/api/responses'
import { ok } from '../src/api/Result'
import type { Result } from '../src/api/Result'
import type { ResponseError } from '../src/api/ResponseError'

const HUMAN = 'alexander.baumann@aimel.com'

function email(overrides: Partial<EmailItemResponse> = {}): EmailItemResponse {
  return {
    emailUuid: 'email-1',
    threadUuid: 'thread-1',
    author: 'ai_agent',
    state: 'unread',
    sentAt: '2026-09-07T21:24:00+00:00',
    sender: 'claude-0bd9c0c5@aimel.com',
    recipient: HUMAN,
    bodyHtml: '<p>Ready for review.</p>',
    preview: 'Ready for review.',
    ...overrides,
  }
}

function thread(overrides: Partial<ThreadListItemResponse> = {}): ThreadListItemResponse {
  return {
    threadUuid: 'thread-1',
    subject: 'fix the flaky auth test',
    emailCount: 2,
    unreadCount: 1,
    latestEmailUuid: 'email-1',
    session: '0bd9c0c5-5b21-44be-9a3b-2793b5788d05',
    sessionShort: '0bd9c0c5',
    sessionColor: '#77AADD',
    updatedAt: '2026-09-07T21:24:00+00:00',
    ...overrides,
  }
}

const OTHER_SESSION = 'aaaa1111-bbbb-2222-cccc-333344445555'

export const SEED = {
  threads: [
    thread(),
    thread({
      threadUuid: 'thread-2',
      subject: 'ship it behind a flag',
      unreadCount: 0,
      emailCount: 3,
      latestEmailUuid: 'email-2',
      updatedAt: '2026-09-07T20:15:00+00:00',
    }),
    thread({
      threadUuid: 'thread-3',
      subject: 'second session, first thread',
      session: OTHER_SESSION,
      sessionShort: 'aaaa1111',
      unreadCount: 2,
      latestEmailUuid: 'email-3',
      updatedAt: '2026-09-07T19:02:00+00:00',
    }),
    thread({
      threadUuid: 'thread-4',
      subject: 'second session, second thread',
      session: OTHER_SESSION,
      sessionShort: 'aaaa1111',
      unreadCount: 0,
      latestEmailUuid: 'email-4',
      updatedAt: '2026-09-07T18:40:00+00:00',
    }),
  ],
  otherSession: OTHER_SESSION,
}

/** Records what was called so a story can assert the interaction, not just the render. */
export class FakeApi {
  readonly markReadCalls: string[] = []
  readonly replyCalls: { emailUuid: string; html: string }[] = []
  private threadList: ThreadListItemResponse[]
  private emailsByThread: Map<string, EmailItemResponse[]>

  constructor(threadList: ThreadListItemResponse[] = SEED.threads) {
    this.threadList = threadList.map((item) => ({ ...item }))
    this.emailsByThread = new Map(
      this.threadList.map((item) => [
        item.threadUuid,
        [
          email({
            emailUuid: item.latestEmailUuid,
            threadUuid: item.threadUuid,
            state: item.unreadCount > 0 ? 'unread' : 'read',
          }),
        ],
      ]),
    )
  }

  async threads(): Promise<Result<ThreadListItemResponse[], ResponseError>> {
    return ok(this.threadList.map((item) => ({ ...item })))
  }

  async thread(emailUuid: string): Promise<Result<ThreadDetailResponse, ResponseError>> {
    const item = this.threadList.find((candidate) => candidate.latestEmailUuid === emailUuid)!
    return ok({
      threadUuid: item.threadUuid,
      subject: item.subject,
      session: item.session,
      sessionShort: item.sessionShort,
      sessionColor: item.sessionColor,
      emails: this.emailsByThread.get(item.threadUuid)!.map((one) => ({ ...one })),
    })
  }

  async markRead(emailUuid: string): Promise<Result<EmailItemResponse, ResponseError>> {
    this.markReadCalls.push(emailUuid)
    for (const [threadUuid, emails] of this.emailsByThread) {
      const found = emails.find((one) => one.emailUuid === emailUuid)
      if (!found) continue
      found.state = 'read'
      const item = this.threadList.find((candidate) => candidate.threadUuid === threadUuid)!
      item.unreadCount = Math.max(0, item.unreadCount - 1)
      return ok({ ...found })
    }
    throw new Error(`story seed has no email ${emailUuid}`)
  }

  async reply(emailUuid: string, html: string): Promise<Result<ReplyAcceptedResponse, ResponseError>> {
    this.replyCalls.push({ emailUuid, html })
    const entry = [...this.emailsByThread.entries()].find(([, emails]) =>
      emails.some((one) => one.emailUuid === emailUuid),
    )!
    const [threadUuid, emails] = entry
    const reply = email({
      emailUuid: `reply-${this.replyCalls.length}`,
      threadUuid,
      author: 'human',
      sender: HUMAN,
      recipient: 'claude-0bd9c0c5@aimel.com',
      bodyHtml: html,
      preview: html,
      // Unread, because unread is the RECIPIENT's queue. A reply the human sent is waiting for the
      // agent, and must not count as unread for the human -- see the story that asserts this.
      state: 'unread',
      sentAt: '2026-09-07T21:30:00+00:00',
    })
    emails.unshift(reply)
    return ok({ emailUuid: reply.emailUuid, threadUuid })
  }
}


/**
 * Installs the stub over `globalThis.fetch` and hands back the recorder plus a restore function.
 * Stories call `restore()` on teardown so one story cannot leak into the next.
 */
export function stubFetch(api: FakeApi = new FakeApi()): { api: FakeApi; restore: () => void } {
  const real = globalThis.fetch

  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = typeof input === 'string' ? input : input.toString()
    const method = init?.method ?? 'GET'
    const body = init?.body ? JSON.parse(String(init.body)) : {}

    const result = await route(api, method, path, body)
    if (!result) {
      return new Response(JSON.stringify({ error: `no stub for ${method} ${path}` }), { status: 404 })
    }
    // Real Response objects, so the client's own status and shape handling runs unchanged.
    return new Response(JSON.stringify(result.body), {
      status: result.status,
      headers: { 'Content-Type': 'application/json' },
    })
  }) as typeof fetch

  return { api, restore: () => { globalThis.fetch = real } }
}

const THREAD_PATH = /^\/api\/emails\/([^/]+)\/thread$/
const REPLY_PATH = /^\/api\/emails\/([^/]+)\/replies$/
const READ_PATH = /^\/api\/emails\/([^/]+)\/read$/

async function route(
  api: FakeApi,
  method: string,
  path: string,
  body: { html?: string },
): Promise<{ status: number; body: unknown } | null> {
  const bare = path.split('?')[0]

  if (method === 'GET' && bare === '/api/threads') {
    return { status: 200, body: unwrap(await api.threads()) }
  }
  const threadMatch = THREAD_PATH.exec(bare)
  if (method === 'GET' && threadMatch) {
    return { status: 200, body: unwrap(await api.thread(threadMatch[1])) }
  }
  const readMatch = READ_PATH.exec(bare)
  if (method === 'POST' && readMatch) {
    return { status: 200, body: unwrap(await api.markRead(readMatch[1])) }
  }
  const replyMatch = REPLY_PATH.exec(bare)
  if (method === 'POST' && replyMatch) {
    if (!body.html?.trim()) {
      // Matches the real api: an empty body is a 422, not a silent success.
      return { status: 422, body: { error: 'html is required' } }
    }
    return { status: 201, body: unwrap(await api.reply(replyMatch[1], body.html)) }
  }
  return null
}

function unwrap<T>(result: Result<T, ResponseError>): T {
  if (result.kind !== 'ok') throw new Error('the fake api should not produce errors')
  return result.value
}
