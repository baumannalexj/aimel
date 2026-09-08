# worklog

One file per ticket. Agents read their own ticket and nothing else here.

Base branch: `improvement/spa-mvp`. Work in `.worktrees/<branch>`. Never touch `~/_claude-email` —
that is the only copy of the real mail. Never `npm install`.

`SEAM —` at the top of a file means the signature is settled and the body is yours.

| ticket | what | owns |
|---|---|---|
| [UI-1](UI-1-timestamp-and-colors.md) | timestamp format, per-participant pill colour | `domain/Timestamp.ts`, `domain/ParticipantColor.ts` |
| [UI-2](UI-2-clickable-card.md) | click-anywhere containers by composition | `components/composition/*` |
| [UI-3](UI-3-email-pane.md) | the email pane: nested message stack, reply placement | `components/emailpane/*` |
| [UI-4](UI-4-default-thread-on-load.md) | open the newest thread on load | `app/pages/*` |

UI-3 depends on UI-1's two seams. Code against the signatures; they will not change.
