# Feature list

Living checklist. `architecture.md` covers *how*; this covers *what*.

## Shipped

### Mail plumbing
- [x] Mailpit container as SMTP intake on `:1025` and HTML viewer on `:8025`, pinned to v1.31.1
- [x] Mail database location prompted on `up`, previous answer offered as the default
- [x] Settings persisted to `~/.config/aimel/settings.json`, every key overridable by `AIMEL_<KEY>`
- [x] `drain` claims spool mail into our store, idempotent on RFC Message-ID
- [x] Captured `Date` preserved on drain rather than stamping `now()`

### Storage
- [x] This service owns its mail in `<mail_dir>/inbox/mail.db`
- [x] One table per state: `unread`, `read`, `deleted`
- [x] Soft delete only — a row moves to `deleted`, nothing is ever removed
- [x] `read_at` and `deleted_at` stamped by DDL defaults, `NOT NULL`, not by application code
- [x] `previous_state` recorded on delete, so "deleted while unread" stays distinguishable
- [x] Autocommit on for the shared session
- [x] `transaction()` opens a *new* session with autocommit off, yields a client bound to it,
      commits on clean exit and rolls back on any exception
- [x] Explicit SQL with named bind parameters, no string interpolation of values

### Correspondence
- [x] One thread per deliverable, subject scoped `<session8>: <title>`
- [x] Reply chains via `In-Reply-To` / `References`
- [x] Thread history embedded in each reply, newest first, in a collapsible block
- [x] `X-<Service>-Session`, `X-<Service>-Thread` and `X-Tags` headers for filtering
- [x] `history` includes deleted messages
- [x] Session uuid detected from the newest Claude transcript, overridable

### Presentation
- [x] Per-session hex colour from a hash, using Paul Tol's colourblind-safe light palette
- [x] Light tint, never bold; honours `NO_COLOR` and non-TTY

### Developer experience
- [x] Hexagonal layout with a manual composition root, no DI framework
- [x] One model per shape, no nullable domain fields
- [x] `uv` for a pinned interpreter and reproducible environment
- [x] Skill installed to `~/.claude/skills/aimel` so every session picks it up
- [x] Service name is config, not a literal in source

## Next

- [ ] **Our own HTML view.** The only real fix for collapsing threads in a list — Mailpit renders a
      flat capture list with no grouping. Blocks the item below.
- [ ] **Turn on `purge_after_drain`.** Deliberately off while Mailpit's UI is the only reader; mail
      currently lives in both stores.
- [ ] **Automated tests.** None exist yet. The repository state machine and the transaction
      rollback path are the two places most worth covering.

## Backlog

- [ ] Full-text search over bodies
- [ ] Attachments
- [ ] Our own SMTP listener, dropping the Mailpit dependency entirely
- [ ] Cross-session inbox, so one view spans every agent
- [ ] Pydantic at the edges where wire validation earns its weight
- [ ] Retention: archive or compact very old threads
