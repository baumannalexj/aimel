# UI-8 — one email row per recipient

Status: **not started**

State is per-recipient, so the row should be too. Right now one email is one row with a single
`recipient` and a single state, which forces every "is this unread for me" question into the SQL.
Replace that with one persisted email per addressee, each carrying its own state.

This supersedes a fix already on `improvement/spa-mvp`: `SELECT_THREADS_FOR_MAILBOX` currently counts
`unread AND recipient = :recipient`. **Delete that condition** as part of this — it is the workaround
this ticket removes. Keep its behaviour though, and keep its tests passing:
`test/adapters/repository/test_reply_does_not_notify_its_author.py` asserts that replying does not
notify its own author and that the agent still sees the reply waiting. Those must stay green through
the redesign; they are the contract, not the implementation.

## Shape

- **`to_users` is always a list**, never a scalar, even for one addressee. A list-of-one is cheap; a
  field that is sometimes a list is where the bugs live.
- Entries are **either an email address or a user uuid**. The resource validates at the edge:
  `try_parse_email` / `try_parse_uuid`. An email resolves to a uuid through a service call. Neither
  parses → 422, naming which entry was bad.
- Only then is the `SendEmail` command constructed, with uuids only. No strings-that-might-be-emails
  reach the domain.
- The repository persists **one row per user in `to_users`**, batched in one transaction. Either all
  recipients get the mail or none do — a half-delivered email is worse than a failed send.
- Polling stays per-user and needs no recipient filter: a user only ever sees their own rows, so they
  never see the copy addressed to someone else.

## What you need to work out and report

- **Where user uuids come from.** There is a sessions table (`sqlite_session_repository.py`) but no
  users table. Say whether you added one or resolved against sessions, and why.
- **What identity means now.** Today one email is one `uuid`. With N rows per email, decide whether
  the copies share a message identity or each get their own, and what that does to `In-Reply-To` and
  `References` threading — RFC message ids are how mail clients thread, and an agent replying quotes
  one. Get this wrong and threads fork.
- **Migration.** The user's real store at `~/_claude-email` is the ONLY copy of their mail. Do not
  touch it, do not write a migration that runs against it. Say what a migration would need to do and
  stop there.

## Done means

`uv run python -m unittest discover -s test -t .` exits 0, the two existing author-notification tests
still pass unmodified, and you add tests for: a two-recipient send persisting two rows, one recipient
reading without changing the other's state, an unparseable entry returning 422, and an email address
resolving to the same row a uuid would.

Verify against a **copy** only — `dataclasses.replace` the loaded config's `database.path`.

Then set Status above to **done** with what you decided on the three questions.
