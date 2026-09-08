import type { ClaudeSession } from '../domain/ClaudeSession'
import type { Comparator } from '../domain/Ordering'
import { sorted } from '../domain/Ordering'

interface Props {
  sessions: ClaudeSession[]
  selectedSessionUuid: string | null
  /** The caller decides the order. This component does not know what "recent" means. */
  ordering: Comparator<ClaudeSession>
  onChange: (sessionUuid: string | null) => void
}

function optionLabel(session: ClaudeSession): string {
  return `${session.shortUuid} · ${session.label()}`
}

export function SessionFilter({ sessions, selectedSessionUuid, ordering, onChange }: Props) {
  if (sessions.length === 0) return null

  return (
    <select
      className="session-filter"
      aria-label="Filter the inbox to one session"
      value={selectedSessionUuid ?? ''}
      onChange={(event) => onChange(event.target.value || null)}
    >
      <option value="">All sessions</option>
      {sorted(sessions, ordering).map((session) => (
        <option
          key={session.sessionUuid}
          value={session.sessionUuid}
          style={{ color: session.color() }}
        >
          {optionLabel(session)}
        </option>
      ))}
    </select>
  )
}
