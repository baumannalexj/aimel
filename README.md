# aimel

Local email for talking to Claude agents. This service owns the mail in SQLite; a
[Mailpit](https://mailpit.axllent.org/) container is the SMTP intake. Nothing leaves the machine and
there are no accounts — any address at the configured domain just works.

## Run

Everything goes through `uv`; there are no wrapper scripts.

```sh
git clone git@github.com:baumannalexj/aimel.git && cd aimel
uv sync                      # installs the project and its groups
uv run aimel up              # prompts for the mail database dir, remembers the answer
uv run aimel install-skill    # drops the agent contract in ~/.claude/skills/aimel
uv run aimel serve            # the reply client, http://localhost:8025
```

From anywhere else, point `uv` at the project — it keeps your working directory, which matters
because session detection reads `cwd`:

```sh
uv run --project ~/sideprojects/aimel aimel poll
```

| Port | Use |
|---|---|
| `1025` | SMTP — everything is sent here |
| `8025` | `aimel serve` — the reply client, threads collapsed. This is the one you open. |
| `8027` | Mailpit viewer and REST API — the raw intake spool, only needed by `drain` |

## Threads are anchored to emails

You open a thread, then reply to a specific email by id. There is no thread name: the thread's uuid
lives in the database and a reply inherits it from whatever email it answers.

```sh
uv run aimel send --title "fix the flaky auth test" --html "<p>Reproduced it.</p>"
#   email  1d2addc5-…      thread 41d01f80-…

uv run aimel reply 1d2addc5-… --html "<p>Fixed and green.</p>"   # as the agent
uv run aimel say   1d2addc5-… --html "<p>ship it</p>"            # as you
```

`--title` becomes the subject, set once when the thread opens; replies reuse it. Replies chain
through `In-Reply-To`/`References` and embed the thread history, newest first, in a collapsible
block. Pass `--no-history` to skip that.

## Commands

| | |
|---|---|
| `send --title "…" --html "…"` | open a thread |
| `reply <email_id> --html "…"` | continue it as the agent |
| `say <email_id> --html "…"` | continue it as you |
| `poll [--as-human]` | unread mail, newest first |
| `read <email_id>` | print it, move it to the read table |
| `delete <email_id>` | soft delete — stamps `deleted_at`, removes nothing |
| `deleted` | what has been soft-deleted |
| `history <email_id>` | the whole thread, newest first, deleted included |
| `threads` | one row per thread, with the latest email id to reply to |
| `drain [--purge]` | claim spool mail into our store, threading by `In-Reply-To` |
| `serve [--port]` | the reply client |
| `up` / `down` / `restart` / `logs` | spool lifecycle |
| `status` / `settings [--set k=v]` | resolved config |

`--json` works on the read commands. `--session <uuid>` overrides session detection.

## Tests

```sh
uv run python -m unittest discover -s test -t .
```

`test/` mirrors `src/`, so a file's tests are findable by path alone.

## Session detection

Agents get no session id in the environment, so `aimel` takes the newest transcript under
`~/.claude/projects/` — preferring the project directory matching `cwd`, then falling back
machine-wide. Right for one active session; with several, pass `--session` or set `AIMEL_SESSION`.

## Settings

Saved to `~/.config/aimel/settings.json`. Any key is overridable by an `AIMEL_<KEY>` env var.

| Key | Default |
|---|---|
| `mail_dir` | `~/_claude-email` — holds `mailpit.db` and `inbox/mail.db` |
| `domain` | `aimel.com` |
| `human_address` | `{user}@{domain}` |
| `agent_address` | `claude-{session8}@{domain}` |
| `subject_template` | `{title}` |
| `smtp_host` / `smtp_port` | `localhost` / `1025` |
| `api_base` | `http://localhost:8025` |
| `purge_after_drain` | `false` |

Addresses and subjects template over `{service}`, `{user}`, `{domain}`, `{session}`, `{session8}`,
`{title}`. Your own address derives from the OS username at runtime, so it is never committed here.

## Storage

Ours is `<mail_dir>/inbox/mail.db`, one table per state (`unread`, `read`, `deleted`). SQLite is
embedded — no server, no port. Read it any time:

```sh
sqlite3 ~/_claude-email/inbox/mail.db "select subject, author, sent_at from unread limit 5;"
```

Mail currently lives in both our store and the spool, because `purge_after_drain` is off while the
Mailpit viewer is still useful.

## Requirements

Docker and [uv](https://docs.astral.sh/uv/). The only third-party dependency is pydantic, scoped to
the `adapters` group. On a Mac running Colima, `docker compose` often is not installed as a plugin;
the runtime falls back to the standalone `docker-compose` binary automatically.
