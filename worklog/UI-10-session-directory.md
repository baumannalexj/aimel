# UI-10 — session directory and filter

Status: **not started**

A dropdown of every Claude session on this machine, most recently active first, that filters the
inbox to one session and can start a new thread with it.

## No hook is needed, and no agent has to seed it

Claude Code already writes every session to disk:

```
~/.claude/projects/<encoded-cwd>/<session-uuid>.jsonl
```

451 transcripts across 12 project dirs on this machine right now. That is the source of truth, read
at runtime. A hook would only be needed to *push* a notification into a session, which is a separate
question and not this ticket.

Per session, from the file alone:
- **uuid** — the filename.
- **last active** — the file's mtime. This is the sort key.
- **project** — the parent directory name, which is the cwd with `/` replaced by `-`. Decode it back
  to a path for display.
- **context/name** — the first user message in the transcript. Read it by scanning from the start for
  the first `{"type":"user"}` line with string content. **Do not read whole files**: some are large,
  there are 451 of them, and a directory listing that stats 451 files and slurps each one will feel
  broken. Read only as far as the first user message, and cap it.

Note the shape varies: not every line has `cwd` or a `message`, and subagent transcripts live under a
`subagents` dir with non-uuid filenames. Skip what you cannot parse rather than failing the listing.

## Surfaces

- **`GET /api/sessions`** — `[{ sessionUuid, shortUuid, project, context, lastActiveAt }]`, most
  recent first, with a `limit`. Mirror it verbatim in `web/src/api/responses.ts` with a shape guard,
  and add a repository method returning a domain model. Components never see a `*Response`.
- **A dropdown filter in the sidebar**, not a separate page — the user asked for a tab and then
  corrected to a dropdown. Selecting a session filters the thread list to that session; clearing it
  restores everything. Colour each option with `hashToHex(sessionUuid)` so the dropdown and the
  existing chips agree.
- **Filtering is a route**, so it is linkable and survives back/forward: `/inbox?session=<uuid>`.
  Follow `app/routes.ts`; today it matches on pathname only, so query handling may need adding.

## Explicitly out of scope

Composing a new thread to a chosen session. It needs a compose UI and the send endpoint that UI-9
touches. Get the directory and the filter working first; say in your report what the smallest compose
addition would be.

## Don't

Do not read from `~/_claude-email` — irrelevant here, and it is the only copy of the user's mail. Do
not add dependencies. Do not stop the servers on 8026/8027.

## Done means

Full python suite exits 0 with tests for the transcript parsing, using a temp directory of fixture
transcripts, including a malformed line and a file with no user message. `npx tsc -b` and
`npx vite build` both exit 0. Verify the endpoint returns real sessions from this machine, and report
how long the listing takes with all 451.

Then set Status above to **done**.
