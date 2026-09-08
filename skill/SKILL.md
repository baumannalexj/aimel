---
name: aimel
description: Correspond with the human over local email instead of only the terminal. Use when reporting progress, results, or deliverables asynchronously, or when checking for replies the human sent by email. Invoke when the user says "email me", "send that to my inbox", "check aimel", or "reply on that thread".
---

# aimel

Local email for agent↔human correspondence. This service owns the mail in SQLite; a Mailpit container
is the SMTP intake and the HTML viewer. Nothing leaves the machine.

`aimel` is the repo's `bin/aimel`. Prefer the absolute path the human gave you; otherwise
`~/sideprojects/aimel/bin/aimel`.

## Threads are anchored to emails, not names

You open a thread, then **reply to a specific email by its id**. There is no thread name to pass —
the thread id lives in the database and is inherited from whatever email you answer.

```sh
# open a thread; --title becomes the subject, set once and never changed
aimel send --title "fix the flaky auth test" \
  --html "<h2>Reproduced</h2><p>The fixture leaks a clock stub.</p>"
# -> email  1d2addc5-…    thread 41d01f80-…

# continue it by answering that email
aimel reply 1d2addc5-… --html "<p>Fixed and green.</p>"
```

Replies chain by `In-Reply-To`/`References` and automatically embed the thread history, newest first,
in a collapsible block — so the newest email is always self-contained. Pass `--no-history` to skip it.

## How much to split

One thread per unit of work that could ship or be abandoned on its own. Facets of the same
deliverable — "how should we store state", "what about deletes" — are replies on that deliverable's
thread, not new threads. Getting this wrong in the noisy direction is the common failure: several
threads for one project loses the human's through-line. When in doubt, reply.

The human's own instructions may tighten this further; theirs win.

## Reading

Nothing waiting is the normal case — do not treat it as an error, and never poll in a loop.

```sh
aimel poll                    # unread for this session, newest first
aimel poll --json             # machine-readable
aimel read <email_id>         # full body; moves it to the read table
aimel threads                 # open threads, with the latest email id to reply to
aimel history <email_id>      # the whole thread, newest first, deleted included
```

## Deleting is soft

`delete` stamps `deleted_at` and moves the row to the `deleted` table. Nothing is ever removed, and
deleted mail still appears in `history`.

```sh
aimel delete <email_id>
aimel deleted
```

## Write for a human reading HTML

The UI renders HTML, so use it: a short `<h2>`, tight `<ul>` for findings, `<pre>` for diffs and
logs. Lead with anything that needs a decision, and name who owns it. Put what you plan to do next
last, in one line, so it can be redirected cheaply. The human may only read the list-view snippet.

## When it is not running

Commands exit non-zero with a hint if the database or spool is unreachable. Start it with
`aimel up`, which prompts for the mail database directory and remembers the answer. Do not install
anything or invent a second mail server — ask the human if `up` fails.
