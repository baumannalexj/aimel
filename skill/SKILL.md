---
name: aimel
description: Correspond with the human over local email instead of only the terminal. Use when work splits into separately shippable deliverables that each deserve their own thread, when reporting progress or results asynchronously, or when checking for replies the human sent by email. Invoke when the user says "email me", "send that to my inbox", "check aimel", or "reply on that thread".
---

# aimel

Local email for agent↔human correspondence. Mail is owned by this service in SQLite; a Mailpit
container is the SMTP intake and the HTML viewer. Nothing leaves the machine.

`aimel` is the repo's `bin/aimel`. Prefer the absolute path the human gave you; otherwise
`~/sideprojects/aimel/bin/aimel`.

## One thread per deliverable

A thread is **one unit of work that could ship or be abandoned on its own** — not one question, not
one message, not one thought.

Apply this test before opening a thread: *if this got cancelled, would the other work still make
sense?* If yes, it is its own thread. If no, it belongs on an existing one.

- ✅ "migrate the billing service" and "fix the flaky auth test" — separate, unrelated deliverables.
- ❌ "how should we store state", "what about deletes", "which library" — these are all facets of one
  deliverable. They go on that deliverable's thread as replies.

Getting this wrong in the noisy direction is the common failure: six threads for one project is worse
than one, because the human loses the through-line. When in doubt, reply on the existing thread.

Subjects carry the session so the human can tell your threads apart:

```
<session8>: <title>
```

Every message also carries `X-<Service>-Session` (full uuid), `X-<Service>-Thread` (slug) and
`X-Tags` (slug, which Mailpit turns into a sidebar filter).

## Open a thread

`--title` opens it; the slug derives from the title unless you pass `--thread`.

```sh
aimel send --title "fix the flaky auth test" \
  --html "<p>Reproduced it — the fixture leaks a clock stub. Plan inside.</p>"
```

## Continue one

Omit `--title` once it exists. Replies chain by `In-Reply-To`/`References` and automatically embed the
thread history, newest first, in a collapsible block — so the newest mail is always self-contained.

```sh
aimel send --thread fix-the-flaky-auth-test --html "<p>Fixed and green.</p>"
aimel history --thread fix-the-flaky-auth-test     # newest first, includes deleted
```

## Check for replies

Nothing waiting is the normal case — do not treat it as an error.

```sh
aimel poll                    # unread for this session
aimel poll --json             # machine-readable
aimel read <id>               # full body; moves it to the read table
aimel threads                 # what is already open
```

## Deleting is soft

`delete` stamps `deleted_at` and moves the row to the `deleted` table. Nothing is ever removed, and
deleted mail still shows in `history`.

```sh
aimel delete <id>
aimel deleted                 # what has been soft-deleted
```

## Write for a human reading HTML

The UI renders HTML, so use it: a short `<h2>`, tight `<ul>` for findings, `<pre>` for diffs and
logs. Lead with the answer — the human may only read the snippet in the list view. Keep a thread's
subject stable; restating the topic in every reply is noise.

## When it is not running

Commands exit non-zero with a hint if the database or spool is unreachable. Start it with
`aimel up`, which prompts for the mail database directory and remembers the answer. Do not install
anything or invent a second mail server — ask the human if `up` fails.
