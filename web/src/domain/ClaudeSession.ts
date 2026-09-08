import type { SessionListItemResponse } from '../api/responses'
import { hashToHex } from './ParticipantColor'

/** One Claude Code session found on disk, for the directory dropdown. */
export class ClaudeSession {
  sessionUuid: string
  shortUuid: string
  project: string
  /** Claude Code's own session name, the one /status shows. Empty until it has generated one. */
  name: string
  context: string
  lastActiveAt: string

  constructor(
    sessionUuid: string,
    shortUuid: string,
    project: string,
    name: string,
    context: string,
    lastActiveAt: string,
  ) {
    this.sessionUuid = sessionUuid
    this.shortUuid = shortUuid
    this.project = project
    this.name = name
    this.context = context
    this.lastActiveAt = lastActiveAt
  }

  static fromResponse(response: SessionListItemResponse): ClaudeSession {
    return new ClaudeSession(
      response.sessionUuid,
      response.shortUuid,
      response.project,
      response.name,
      response.context,
      response.lastActiveAt,
    )
  }

  /** The session's own name when it has one, otherwise its opening prompt. */
  label(): string {
    return this.name || this.context || '(no prompt yet)'
  }

  /** Derived, never stored: a second copy of a colour can only drift from the hash. */
  color(): string {
    return hashToHex(this.sessionUuid)
  }
}
