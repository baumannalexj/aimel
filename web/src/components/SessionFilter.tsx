import type { ClaudeSession } from '../domain/ClaudeSession'
import type { Comparator } from '../domain/Ordering'
import { sorted } from '../domain/Ordering'
import { hashToHex } from '../domain/ParticipantColor'

interface Props {
  sessions: ClaudeSession[]
  selectedSessionUuid: string | null
  /** The caller decides the order. This component does not know what "recent" means. */
  ordering: Comparator<ClaudeSession>
  onChange: (sessionUuid: string | null) => void
}

function optionLabel(session: ClaudeSession): string {
  return `${session.shortUuid} · ${session.project} — ${session.context || '(no prompt yet)'}`
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
          style={{ color: hashToHex(session.sessionUuid) }}
        >
          {optionLabel(session)}
        </option>
      ))}
    </select>
  )
}
