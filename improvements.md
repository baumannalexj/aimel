# Improvement list

Living checklist. `architecture.md` covers *how*; this covers *what*, and what is still owed.

## Future improvements

Raised in review, not yet done.

- [ ] **Partial rendering, then optionally a SPA.** Today every interaction is a full page render:
      reply is `POST -> 303 -> GET`, so the whole thread re-renders to add one email. Two steps, and
      the first is most of the value:
      - **Fragment SSR.** Routes return a rendered component rather than a page, and the client swaps
        it in. Still no client-side models and no JSON API — the server keeps owning HTML, so the
        component tree and props dataclasses are reused as they are. htmx is the obvious vehicle; the
        cost is a second render path per component and a JS dependency.
      - **A real SPA.** JSON endpoints, client-side models, a JS client (`repository/emailClient.js`
        wrapping fetch with one place for error handling), client routing. This is what makes
        `web/models/` meaningful — until then there is nothing for it to hold, because the server
        renders and the browser never owns state.

      Worth noting the ordering: the resource already separates "map domain to props" from "render",
      so fragment SSR is a routing change rather than a rewrite. A SPA additionally needs the response
      shapes designed as an API, which is a bigger commitment than it looks.
- [ ] **Make the schema relational: fetch by thread id and join.** Today each state table holds a
      full copy of every column, so reading a thread is a `UNION ALL` of three wide selects and
      "get the emails on this thread" is not a join at all. The relational shape keeps the
      table-per-state idea but stores state as a *reference* rather than a copy:

      ```
      threads(pk, uuid, subject, created_at)
      emails (pk, uuid, thread_pk -> threads.pk, session, sender, recipient,
              actor, rfc_message_id, in_reply_to, refs, body_html, body_text, sent_at, created_at)
      unread (email_pk -> emails.pk)
      read   (email_pk -> emails.pk, read_at)
      deleted(email_pk -> emails.pk, deleted_at, previous_state)
      ```

      Then a thread is one join on `thread_pk`, a state change moves a single narrow row, the subject
      lives once instead of on every email, and `SELECT *` stops carrying eleven duplicated columns
      per state. `IEmailRepository` should not change shape, so this is a repository-and-schema job
      plus a rebuild from the spool.

- [ ] **Swap the hand-rolled HTTP server for FastAPI.** Decided FastAPI over Flask, deferred — "fast
      but we should get back to this". `WebServer` is a `BaseHTTPRequestHandler` with hand-written
      routing, which is exactly what the hex boundary exists to make replaceable: `EmailWebResource`
      renders and `EmailCliResource` marshals, so a framework only owns routing and serialisation.
      The request DTOs are already pydantic, so FastAPI gets validation and `/docs` for free.
      `uv add --group adapters fastapi uvicorn`.
- [ ] **Ship a `docker-compose.yml` as well as `compose.yml`.** Colima installs the standalone
      `docker-compose` binary rather than the `docker compose` plugin. Our v5.1.4 standalone does read
      `compose.yml`, and `DockerComposeRuntime` already prefers that binary, so nothing is broken —
      but older standalone versions only look for `docker-compose.yml`, and the filename is what
      people expect. Open question: symlink, rename, or leave it.
- [ ] **Review comments now resolved, kept for the record**
      ([requests.py L41-L46 @ review-comments](https://github.com/baumannalexj/aimel/blob/review-comments/src/adapters/resource/requests.py#L41-L46),
      [L73](https://github.com/baumannalexj/aimel/blob/review-comments/src/adapters/resource/requests.py#L73),
      [L79](https://github.com/baumannalexj/aimel/blob/review-comments/src/adapters/resource/requests.py#L79)):
      "should be a UUID" and "can this be a UUID" / "make uuid" — done, `session` and `email_id` are
      required pydantic `UUID` fields with no default. "try to avoid booleans - use Actor enum like
      HUMAN | CLAUDE" — done as `Actor(HUMAN | AI_AGENT)`. "use an enum like IncludeHistory NONE |
      ALL" — done. "what's different from html and test?" — `html` is the rendered body, `text` is
      only the plain-text alternative part and is derived from `html` when omitted; documented in the
      module docstring. "I think you can also change subject" — deliberately not: the subject is the
      thread's context, fixed when the thread opens.
- [x] **Drop `--text` from the CLI.** Follows from the answer above: it is derived, so the flag earned
      nothing and invited confusion. Removed from `send`/`reply`/`say` and from the request models;
      `EmailSendNewThread`/`EmailReply` no longer carry `body_text` either, since nothing outbound set
      it. `body_text` stays on `SentEmail`/`Correspondence` (derived from `body_html` at send time) and
      on the captured/drained side, where Mailpit's real text part is still worth keeping.
- [x] **Require a body.** `html` no longer defaults to `""` — it is `Field(min_length=1)` on both
      `SendNewThreadRequest` and `ReplyRequest`, the same "should blow up if not provided" argument
      that fixed the uuid fields. The web reply form still redirects on a blank submission because
      `WebServer` guards on the stripped form value before it ever reaches the request model.

## Shipped

### Mail plumbing
- [x] `drain` strips the quoted history before persisting — Mailpit captures the *rendered* body, so
      importing it verbatim duplicated the whole thread into every reply (16 of 50 rows were carrying
      one). Existing rows keep theirs until the next rebuild.
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
- [x] `HtmlBody` value object — pydantic ships no HTML type, so tag-stripping, plain-text derivation
      and preview generation live here instead of being duplicated in the transport and the model
- [x] `Actor` enum (`HUMAN` | `AI_AGENT`) replacing the `as_human` boolean, carried on the wire as
      `X-<Service>-Actor` so intake can restore who wrote what
- [x] `IncludeHistory` enum (`NONE` | `ALL`) replacing the `include_history` boolean
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

### Web view
- [x] `aimel serve` on `:8026` — threads collapsed into one row each, which Mailpit's flat capture
      list cannot do
- [x] Reply from the browser: Mailpit has no compose at all (`MessageRelay.Enabled: false`), so this
      is the only way to answer an agent without the CLI
- [x] Empty submissions redirect rather than sending a blank email
- [ ] Bound to 127.0.0.1 with no auth — it holds unauthenticated mail, so keep it local

### Presentation
- [x] Per-session hex colour from a hash, using Paul Tol's colourblind-safe light palette
- [x] Light tint, never bold; honours `NO_COLOR` and non-TTY

### Developer experience
- [x] `uv run aimel` as the only entrypoint — no wrapper scripts; `up`/`down`/`restart`/`logs`/
      `install-skill`/`open` are Python commands behind an `IContainerRuntime` port
- [x] Installed editable, so source edits need no re-sync
- [x] SQL in triple-quoted statements in `adapters/repository/sql/`, values always named binds, and
      `IDatabaseClient.identifier()` validating the one place a table name varies
- [x] Hexagonal layout with a manual composition root, no DI framework
- [x] One model per shape, no nullable domain fields
- [x] `uv` for a pinned interpreter and reproducible environment
- [x] Skill installed to `~/.claude/skills/aimel` so every session picks it up
- [x] Service name is config, not a literal in source

## Next


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
- [ ] **More tests.** Two exist (`uv run python -m unittest discover -s test -t .`): `InboxService.read` delegation, and
      `SqliteEmailRepository.soft_delete` proving the statements run on the transaction client.
      Untested: `send_email` chain building, `drain` idempotency, the marshaller.

## Backlog

- [ ] Full-text search over bodies
- [ ] Attachments
- [ ] Our own SMTP listener, dropping the Mailpit dependency entirely
- [ ] Cross-session inbox, so one view spans every agent
- [ ] Pydantic at the edges where wire validation earns its weight
- [ ] Retention: archive or compact very old threads
