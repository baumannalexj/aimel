# board

UI first. Backend only when a UI ticket is blocked without it.

Base branch `improvement/spa-mvp`. Worktree per ticket at `<repo>/.worktrees/<branch>`.
**Agents: edit the `Status` line of your own ticket file when you finish. Nothing else in worklog/.**

Standing rules: never touch `~/_claude-email` (only copy of the real mail) · never `npm install` ·
`SEAM —` at the top of a file means the signature is settled and the body is yours · the
chrome-devtools MCP browser is shared between agents, use an isolated Playwright browser instead.

Running now: UI on [8026](http://127.0.0.1:8026/), API on 8027, both out of `.worktrees/spa-mvp`.

## P1 — you cannot read your mail properly without these

| ticket | what | owns | branch |
|---|---|---|---|
| [UI-1](UI-1-timestamp-and-colors.md) | timestamp format, per-participant colour | `domain/Timestamp.ts`, `domain/ParticipantColor.ts` | `improvement/ui-timestamp-colors` |
| [UI-2](UI-2-clickable-card.md) | click anywhere in a row, by composition | `components/composition/*`, `ThreadRow.tsx` | `improvement/ui-clickable-card` |
| [UI-3a](UI-3a-pane-header.md) | full session uuid + subject | `components/emailpane/PaneHeader.tsx` | `improvement/ui-pane-header` |
| [UI-3b](UI-3b-message-stack.md) | nested message stack, limit 5 | `components/emailpane/MessageStack.tsx` | `improvement/ui-message-stack` |
| [UI-3c](UI-3c-author-pill.md) | per-author pill | `components/emailpane/AuthorPill.tsx` | `improvement/ui-author-pill` |
| [UI-3d](UI-3d-reply-box.md) | reply top-right, box between latest and latest-1 | `components/emailpane/ReplyBox.tsx` | `improvement/ui-reply-box` |
| [UI-4](UI-4-default-thread-on-load.md) | open the newest thread on load | `app/pages/*` | `improvement/ui-default-thread` |
| [UI-5](UI-5-error-banner.md) | banner: status, message, expandable stack | `app/errors/ErrorBanner.tsx` | `improvement/ui-error-banner` |
| [UI-6](UI-6-router-and-history.md) | real URLs, back and forward | `App.tsx`, `app/Router.tsx`, `app/routes.ts` | `improvement/ui-router-history` |
| [UI-7](UI-7-expose-thread-uuid.md) | `threadUuid` on the email payload, `GET /api/emails/<uuid>` | `adapters/resource/*`, `email_sql.py` | `improvement/ui-thread-uuid` |

`EmailPane.tsx` composes 3a–3d and is owned by the lead, so the four never touch the same file.
UI-3b and UI-3c depend on UI-1's two seams; code against the signatures, they will not change.

## P2 — small UI changes, once P1 renders

| ticket | what |
|---|---|
| [UI-6](UI-6-collapse-thread-list.md) | collapse/group the thread list — it is 24 rows and climbing |
| [UI-7](UI-7-markdown-bodies.md) | render markdown in bodies |
| [UI-8](UI-8-db-size-indicator.md) | size indicator in the footer — needs an API endpoint over `DatabaseStats` |
| [UI-9](UI-9-styling-pass.md) | styling pass against the style guide |

## P3 — V2, not started

New email to a session id · subject change for side quests · notify an agent of a reply plus a
"thinking" ack · search · soft delete from the UI · per-`ResponseError`-kind handling (the kinds and
the `DomainException` variants exist; only the mapping is missing).

## Done

Reply on the real dashboard · inbox scoped to the human with `?scope=all` · session registry ·
router · `DatabaseStats` · error seam (`Result`/`ResponseError`/`DomainException`) · error surface
(banner + toast) · real enums · `EmailRepository` behind the seam · 404 instead of a dropped
connection for an unknown email.
