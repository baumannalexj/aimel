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

### Identity and naming
- [x] Surrogate `pk` plus a schema-generated `uuid` on every table; `created_at` schema-defaulted
- [x] The primary key never leaves the repository — domain objects expose the uuid as `id`
- [x] `thread_uuid` persisted on every row; `EmailThread` is the chain's identity, not its topic
- [x] A thread's uuid is reused across its messages and survives state changes
- [x] `X-Tags` carries the full Claude session uuid, so the sidebar groups by session
- [x] The subject is the thread's context, set once when the thread opens, with no session prefix
- [x] The session is shown as a coloured chip in CLI output rather than baked into the subject
- [x] Existing data migrated: session prefixes stripped from stored subjects

### Domain types
- [x] `DomainModel` marker; every domain object a frozen dataclass
- [x] `Email` with an `address` field, `EmailSubject`, `ThreadSlug`, `SessionId`, `EmailThread`
- [x] Request objects carry domain types, marshalled once at the edge by `CliRequestMarshaller`
- [x] `list_unread` / `list_unread_in_thread` split so the port takes no optional thread

### Correspondence
- [x] One thread per deliverable (the engagement-level rule lives in the caller's own contract)
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
- [ ] **A session registry.** There is no record of which agents exist — an address is inferred from
      whichever transcript was touched last, which is ambiguous with several sessions live. A session
      table would let you list agents, address one deliberately, and is the natural home for a
      persisted per-session colour.
- [ ] **Notify the agent.** Nothing can wake an agent; mail is only seen when it polls. A Claude Code
      hook that injects an unread count at the start of a turn is the only real push.
- [ ] **Pydantic at the edge**, once an HTTP resource exists, with `SendMessageRequest.to_domain()`
      and `SendMessageResponse.ok_no_content()`. Needs the dependency added.
- [ ] **Two remaining nullables.** `PollRequest.thread` and `IEmailRepository.find` still return or
      carry `None`; both want a second shape instead.
- [ ] **More tests.** Two exist (`bin/test`): `InboxService.read` delegation, and
      `SqliteEmailRepository.soft_delete` proving the statements run on the transaction client.
      Untested: `send_email` chain building, `drain` idempotency, the marshaller.

## Backlog

- [ ] Full-text search over bodies
- [ ] Attachments
- [ ] Our own SMTP listener, dropping the Mailpit dependency entirely
- [ ] Cross-session inbox, so one view spans every agent
- [ ] Pydantic at the edges where wire validation earns its weight
- [ ] Retention: archive or compact very old threads
