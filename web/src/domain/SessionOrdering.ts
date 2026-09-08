import type { ClaudeSession } from './ClaudeSession'
import type { Comparator, Predicate } from './Ordering'
import type { ThreadSummary } from './ThreadSummary'

/** Most recently active first. The default, and the only one the dropdown currently offers. */
export class ByLastActiveDescending implements Comparator<ClaudeSession> {
  compare(left: ClaudeSession, right: ClaudeSession): number {
    // ISO-8601 with a fixed offset sorts correctly as a string, so no Date parsing per comparison.
    return right.lastActiveAt.localeCompare(left.lastActiveAt)
  }
}

/** Here to prove the seam is real rather than decorative -- one line to offer it in the dropdown. */
export class ByProjectThenLastActive implements Comparator<ClaudeSession> {
  private readonly byActivity = new ByLastActiveDescending()

  compare(left: ClaudeSession, right: ClaudeSession): number {
    const byProject = left.project.localeCompare(right.project)
    return byProject === 0 ? this.byActivity.compare(left, right) : byProject
  }
}

export class ThreadsOfSession implements Predicate<ThreadSummary> {
  private readonly sessionUuid: string

  constructor(sessionUuid: string) {
    this.sessionUuid = sessionUuid
  }

  matches(thread: ThreadSummary): boolean {
    return thread.session === this.sessionUuid
  }
}

/** Newest activity first, matching how the inbox already reads. */
export class ThreadsByUpdatedDescending implements Comparator<ThreadSummary> {
  compare(left: ThreadSummary, right: ThreadSummary): number {
    return right.updatedAt.localeCompare(left.updatedAt)
  }
}
