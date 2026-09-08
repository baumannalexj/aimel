# UI-9 — unread as its own per-user table

Status: **not started**

**Supersedes UI-8.** `improvement/ui-per-recipient` duplicated the whole email row per addressee.
This replaces that with one email row plus a per-user unread table, which is the normalised version
of the same idea. Read that branch for its `RecipientDirectory` work — the uuid resolution is reusable
— but do not merge it.

## Shape

One email, one row. Recipients live in a join table keyed by user:

```
unread_emails
  id | user_uuid | email_uuid | thread_uuid | created_at
     | zxc       | fromabc-5433 | thread-123 |
     | sdf       | fromabc-5433 | thread-123 |
     | sdf       | frompuo-4922 | thread-039 |   <- sdf has 2 unreads
```

- Sending from `abc` to `[zxc, sdf]` writes **one** email row and **two** `unread_emails` rows.
- Presence in `unread_emails` *is* unread state, per user. No status column, no CASE in a query.
- Opening moves that user's row `unread_emails` -> `read_emails`. Same move-between-tables discipline
  the email states already use.
- Notification is per row, so a user is only ever told about their own.

## What this replaces

`unread`/`read`/`deleted` currently hold the email itself and the state together. Decide and report
whether the email body now lives in one `emails` table with state entirely in the join tables, or
whether you keep the existing state tables and add the join. The first is the real normalisation; say
which you did and why.

Keep these green **unmodified** — they pin the behaviour, not the implementation:
`test/adapters/repository/test_reply_does_not_notify_its_author.py`.

## The left list is not threads

The sidebar today lists threads. On this model it lists **that user's unread emails**. Opening one
shows its thread, reverse chronological. Worth saying out loud because it changes what
`SELECT_THREADS_FOR_MAILBOX` is for, and may retire it.

## Migration

`~/_claude-email` is the ONLY copy of the user's mail. Do not write or run a migration against it.
Describe what one would do and stop. Verify on a copy via `dataclasses.replace` on the config.

## Done means

Full suite exits 0 with tests for: a two-recipient send writing one email and two unread rows, one
user reading without touching the other's unread state, and a user's unread count counting only their
own rows.

Then set Status above to **done** with your answer to the normalisation question.
