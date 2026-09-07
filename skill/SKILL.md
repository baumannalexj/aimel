---
name: aimel
description: Correspond with the human over local email instead of only the terminal. Use when a task splits into separable units of work that each deserve their own thread, when reporting progress or results asynchronously, or when checking for replies the human sent by email. Invoke when the user says "email me", "send that to my inbox", "check aimel", or "reply on that thread".
---

# aimel

Local email for agent↔human correspondence. A Mailpit container is the whole backend: SMTP in on
`:1025`, REST + HTML UI on `:8025`. All mail is local — nothing leaves the machine.

`aimel` is the repo's `bin/aimel`. Prefer the absolute path the human gave you; otherwise
`~/sideprojects/aimel/bin/aimel`.

## The one rule: one thread per thought

A thread is a single unit of work, not a conversation dump. If the human asks for five things and two
are unrelated to the rest, that is **three threads**, opened separately. Never fold an unrelated
follow-up into an existing thread — open a new one and say so.

Subjects carry the session so the human can tell your threads apart:

```
<session8>: <title>
```

Both are set for you. Every message also carries `X-Aimel-Session` (full uuid) and `X-Aimel-Thread`
(slug) for exact filtering.

## Open a thread

`--title` opens it; the slug is derived from the title unless you pass `--thread`.

```sh
aimel send --title "fix the flaky auth test" \
  --html "<p>Reproduced it — the fixture leaks a clock stub. Plan inside.</p>"
```

## Continue one

Omit `--title` once the thread exists. Replies chain by `In-Reply-To`/`References`, so real clients
thread them correctly.

```sh
aimel send --thread fix-the-flaky-auth-test --html "<p>Fixed and green. Diff attached below.</p>"
```

## Check for replies

Poll your own mailbox. Nothing waiting is the normal case — do not treat it as an error.

```sh
aimel poll                    # unread for this session
aimel poll --json             # same, machine-readable
aimel read <id>               # full body, marks it read
aimel threads                 # what you already have open
```

## Write for a human reading HTML

The UI renders HTML, so use it: a short `<h2>`, tight `<ul>` for findings, `<pre>` for diffs and
logs. Lead with the answer — the human may only read the snippet in the list view. Keep one thread's
subject stable; restating the topic in every reply is noise.

## When it is not running

`aimel poll` exits non-zero with a hint if Mailpit is unreachable. Start it with `aimel up`, which
prompts for the mail database directory and remembers the answer. Do not install anything or invent a
second mail server — ask the human if `up` fails.
