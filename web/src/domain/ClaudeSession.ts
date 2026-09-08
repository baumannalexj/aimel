import type { SessionListItemResponse } from '../api/responses'

/** One Claude Code session found on disk, for the directory dropdown. */
export class ClaudeSession {
  sessionUuid: string
  shortUuid: string
  project: string
  context: string
  lastActiveAt: string

  constructor(sessionUuid: string, shortUuid: string, project: string, context: string, lastActiveAt: string) {
    this.sessionUuid = sessionUuid
    this.shortUuid = shortUuid
    this.project = project
    this.context = context
    this.lastActiveAt = lastActiveAt
  }

  static fromResponse(response: SessionListItemResponse): ClaudeSession {
    return new ClaudeSession(
      response.sessionUuid,
      response.shortUuid,
      response.project,
      response.context,
      response.lastActiveAt,
    )
  }
}
