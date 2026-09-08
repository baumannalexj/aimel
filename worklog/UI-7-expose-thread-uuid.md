# UI-7 — surface the thread for an email

Status: **not started**

Deep links need `/emails/<emailUuid>` to resolve to a thread. Backend, kept small because the UI is
the priority.

Own `src/adapters/resource/api_responses.py`, `src/adapters/resource/email_api_resource.py`,
`src/application/api_server.py`, `src/adapters/repository/sql/email_sql.py`, and the matching tests.

## 1. `threadUuid` on the email payload

`EmailItemResponse` does not carry it, so a client holding an email cannot say which thread it is in
without fetching the whole thread. Add it. Then mirror it in `web/src/api/responses.ts` — that file
is a **verbatim** mirror of the python, including its runtime shape guard.

## 2. `GET /api/emails/<emailUuid>`

Returns that email's whole thread, newest first — the same shape `/api/emails/<uuid>/thread`
returns. The user's sketch of the query is a self-join on `thread_uuid`:

```sql
select e1.* from email e1
  join email e2 on e1.thread_uuid = e2.thread_uuid
 where e2.uuid = :email_uuid
 order by e1.sent_at desc
```

Note the shape it has to fit: there is no single `email` table. State is table-per-state
(`unread`/`read`/`deleted`) and a thread's messages can span all three, which is why
`history_for_email` reads each state and merges. Follow that existing pattern rather than the
literal SQL above.

An unknown uuid must return **404**, not drop the connection. `EmailNotFound` already exists and the
handler for `/thread` already maps it — do the same, and add a test, because this exact endpoint had
that bug last week.

## Done means

`uv run python -m unittest discover -s test -t .` exits 0 with new tests covering the 404 and the
happy path. Verify against a **copy** of the database, never `~/_claude-email` — it is the only copy
of the real mail. `dataclasses.replace` the loaded config's `database.path` to point at your copy.

Then set Status above to **done** with one line on anything you decided.
