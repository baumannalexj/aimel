# aimel

Local email for talking to Claude agents. One [Mailpit](https://mailpit.axllent.org/) container is the
whole backend, plus a stdlib-only Python CLI that gives agents a threading contract. Nothing leaves the
machine and there are no accounts — any address at the configured domain just works.

```sh
bin/aimel up                 # prompts for the mail database dir, remembers it
bin/aimel install-skill      # drops the agent contract in ~/.claude/skills/aimel
open http://localhost:8025
```

| Port | Use |
|---|---|
| `1025` | SMTP — everything is sent here |
| `8025` | Web UI + REST API — you read in the browser, agents poll the API |

## One thread per thought

The point of the CLI. A thread is one unit of work, so if you ask for five things and two are
unrelated, an agent opens three threads instead of one mega-message. Subjects are scoped by session:

```
Subject: 0bd9c0c5: fix the flaky auth test
X-Aimel-Session: 0bd9c0c5-5b21-44be-9a3b-2793b5788d05
X-Aimel-Thread: fix-the-flaky-auth-test
```

Replies chain through `In-Reply-To` and `References`, and each thread gets a ledger at
`<mail_dir>/threads/<session8>/<slug>.json` tracking its subject and message ids.

## Commands

| | |
|---|---|
| `aimel send --title "…" --html "…"` | open a thread (agent → you); slug derived from the title |
| `aimel send --thread <slug> --html "…"` | continue it |
| `aimel say --thread <slug> --html "…"` | reply as you (you → agent) |
| `aimel poll [--thread <slug>] [--all]` | unread mail for this session |
| `aimel read <id> [--keep-unread]` | print a message, mark it read |
| `aimel threads` | open threads for this session |
| `aimel status` | resolved config and Mailpit health |
| `aimel up` / `down` / `restart` / `logs` | container lifecycle |
| `aimel settings --set key=value` | change a saved setting |

`--json` works on `poll`, `read`, `threads` and `send` for machine-readable output. Bodies can also be
piped on stdin instead of `--html` / `--text`.

## Session detection

Agents don't get a session id in the environment, so `aimel` takes the newest transcript under
`~/.claude/projects/` — preferring the project directory matching `cwd`, then falling back machine-wide.
That's right for one active session; with several running at once, pass `--session <uuid>` or set
`AIMEL_SESSION`.

## Settings

Saved to `~/.config/aimel/settings.json` (see `settings.example.json`). Any key is overridable by an
`AIMEL_<KEY>` environment variable.

| Key | Default |
|---|---|
| `mail_dir` | `~/_claude-email` — holds `mailpit.db` and the thread ledger |
| `domain` | `aimel.com` |
| `human_address` | `{user}@{domain}` |
| `agent_address` | `claude-{session8}@{domain}` |
| `subject_template` | `{session8}: {title}` |
| `smtp_host` / `smtp_port` | `localhost` / `1025` |
| `api_base` | `http://localhost:8025` |
| `max_messages` | `5000` |

Address and subject values are templates over `{user}`, `{domain}`, `{session}`, `{session8}`,
`{thread}`, `{title}`. Your own address is derived from the OS username at runtime, so it is never
committed here.

## Known rough edge

Mailpit's web UI can render mail but not compose it, so replying to an agent goes through
`aimel say`, not the browser. A small compose page is the obvious next iteration.

## Requirements

Docker and Python 3 — no pip packages. On a Mac running Colima, note that `docker compose` may not be
installed as a plugin; the runner falls back to the standalone `docker-compose` binary automatically.
