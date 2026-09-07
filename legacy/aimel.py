#!/usr/bin/env python3
"""aimel — email correspondence between a human and Claude agents. Stdlib only."""

import argparse
import getpass
import json
import os
import re
import smtplib
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from pathlib import Path

DEFAULTS = {
    "service_name": "aimel",
    "mail_dir": "~/_claude-email",
    "smtp_host": "localhost",
    "smtp_port": 1025,
    "api_base": "http://localhost:8025",
    "domain": "aimel.com",
    "human_address": "{user}@{domain}",
    "agent_address": "claude-{session8}@{domain}",
    "subject_template": "{session8}: {title}",
    "max_messages": 5000,
}

TEMPLATE_VARS = ("service", "user", "domain", "session", "session8", "thread", "title")

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)

SETTINGS_PATH = Path(
    os.environ.get("AIMEL_SETTINGS", Path.home() / ".config" / "aimel" / "settings.json")
)


# --- settings ---

def load_settings():
    settings = dict(DEFAULTS)
    if SETTINGS_PATH.exists():
        settings.update(json.loads(SETTINGS_PATH.read_text()))
    for key in DEFAULTS:
        env = os.environ.get("AIMEL_" + key.upper())
        if env:
            settings[key] = env
    settings["smtp_port"] = int(settings["smtp_port"])
    settings["max_messages"] = int(settings["max_messages"])
    return settings


def save_settings(settings):
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n")


def mail_dir(settings):
    return Path(settings["mail_dir"]).expanduser()


# --- identity ---

def current_user():
    try:
        return getpass.getuser()
    except Exception:
        return os.environ.get("USER", "human")


def project_slug(path):
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def detect_session():
    """The live session is the transcript being written right now — cwd's project dir first."""
    projects = Path.home() / ".claude" / "projects"
    for root in (projects / project_slug(Path.cwd()), projects):
        if not root.is_dir():
            continue
        logs = [p for p in root.glob("**/*.jsonl" if root == projects else "*.jsonl")
                if UUID_RE.fullmatch(p.stem)]
        if logs:
            return max(logs, key=lambda p: p.stat().st_mtime).stem
    return None


def resolve_session(explicit=None):
    session = explicit or os.environ.get("AIMEL_SESSION") or detect_session()
    if not session:
        sys.exit(
            "no session uuid: pass --session, set AIMEL_SESSION, or run from a directory "
            "with a Claude transcript under ~/.claude/projects/"
        )
    return session


def render(template, **extra):
    values = {var: "" for var in TEMPLATE_VARS}
    values.update({k: v for k, v in extra.items() if v is not None})
    try:
        return template.format(**values)
    except KeyError as exc:
        sys.exit(f"unknown template variable {exc} — available: {', '.join(TEMPLATE_VARS)}")


def addresses(settings, session, thread=None, title=None):
    ctx = {
        "service": settings["service_name"],
        "user": current_user(),
        "domain": settings["domain"],
        "session": session,
        "session8": session[:8],
        "thread": thread,
        "title": title,
    }
    return (
        render(settings["human_address"], **ctx),
        render(settings["agent_address"], **ctx),
        ctx,
    )


def slugify(text):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")[:60]


# --- thread ledger ---

def ledger_path(settings, session, thread):
    return mail_dir(settings) / "threads" / session[:8] / f"{thread}.json"


def load_thread(settings, session, thread):
    path = ledger_path(settings, session, thread)
    return json.loads(path.read_text()) if path.exists() else None


def save_thread(settings, record):
    path = ledger_path(settings, record["session"], record["thread"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")


def list_threads(settings, session):
    root = mail_dir(settings) / "threads" / session[:8]
    if not root.is_dir():
        return []
    records = [json.loads(p.read_text()) for p in root.glob("*.json")]
    return sorted(records, key=lambda r: r.get("updated", ""), reverse=True)


# --- mailpit api ---

def api(settings, path, method="GET", payload=None, params=None):
    url = settings["api_base"].rstrip("/") + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data, method=method, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
        if not body:
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"raw": body.decode(errors="replace")}
    except urllib.error.URLError as exc:
        sys.exit(f"cannot reach mailpit at {settings['api_base']} ({exc}) — try: bin/aimel up")


# --- sending ---

def deliver(settings, sender, recipient, subject, body_html, body_text, headers):
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg["Date"] = format_datetime(datetime.now(timezone.utc))
    message_id = make_msgid(domain=settings["domain"])
    msg["Message-ID"] = message_id
    for key, value in headers.items():
        if value:
            msg[key] = value
    msg.set_content(body_text or re.sub(r"<[^>]+>", "", body_html or ""))
    if body_html:
        msg.add_alternative(body_html, subtype="html")
    with smtplib.SMTP(settings["smtp_host"], settings["smtp_port"], timeout=10) as smtp:
        smtp.send_message(msg)
    return message_id


def read_body(args):
    if args.html:
        return args.html, args.text
    if args.text:
        return None, args.text
    if not sys.stdin.isatty():
        piped = sys.stdin.read().strip()
        if piped:
            return (piped, None) if "<" in piped else (None, piped)
    sys.exit("no body: pass --html, --text, or pipe it on stdin")


def post(settings, session, thread, title, body_html, body_text, from_human, with_history=True):
    record = load_thread(settings, session, thread)
    if record is None:
        if not title:
            sys.exit(f"thread '{thread}' is new — pass --title to open it")
        human, agent, ctx = addresses(settings, session, thread, title)
        ctx["title"] = title
        record = {
            "thread": thread,
            "session": session,
            "title": title,
            "subject": render(settings["subject_template"], **ctx),
            "human_address": human,
            "agent_address": agent,
            "message_ids": [],
            "created": now_iso(),
        }
    record.setdefault("messages", [])
    chain = record["message_ids"]
    sender = record["human_address"] if from_human else record["agent_address"]
    recipient = record["agent_address"] if from_human else record["human_address"]
    service = settings["service_name"]
    sent_at = now_iso()
    outgoing = body_html
    if body_html and with_history and record["messages"]:
        outgoing = body_html + render_history(record, settings)
    message_id = deliver(
        settings,
        sender,
        recipient,
        record["subject"],
        outgoing,
        body_text,
        {
            "In-Reply-To": chain[-1] if chain else None,
            "References": " ".join(chain) if chain else None,
            f"X-{service.title()}-Session": session,
            f"X-{service.title()}-Thread": thread,
            "X-Tags": thread,
        },
    )
    chain.append(message_id)
    record["messages"].append(
        {
            "message_id": message_id,
            "from": sender,
            "to": recipient,
            "author": "you" if from_human else "agent",
            "sent_at": sent_at,
            "html": body_html,
            "text": body_text,
        }
    )
    record["updated"] = sent_at
    save_thread(settings, record)
    return record, message_id


def render_history(record, settings):
    """Prior messages newest-first, so the latest mail carries the whole thread."""
    earlier = list(reversed(record["messages"]))
    rows = []
    for entry in earlier:
        body = entry.get("html") or f"<p>{entry.get('text', '')}</p>"
        rows.append(
            f'<blockquote style="margin:0 0 1em;padding:.4em 0 .4em 1em;'
            f'border-left:3px solid #ccc">'
            f'<div style="color:#666;font-size:.85em">{entry["author"]}'
            f' · {entry["sent_at"]}</div>{body}</blockquote>'
        )
    return (
        f'<hr><details open><summary>history · {len(earlier)} earlier, newest first'
        f"</summary>{''.join(rows)}</details>"
    )


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- commands ---

def cmd_send(args, settings):
    session = resolve_session(args.session)
    thread = args.thread or (slugify(args.title) if args.title else None)
    if not thread:
        sys.exit("pass --thread or --title so the correspondence has a thread")
    body_html, body_text = read_body(args)
    record, message_id = post(
        settings, session, thread, args.title, body_html, body_text,
        from_human=args.as_human, with_history=not args.no_history,
    )
    if args.json:
        print(json.dumps({"thread": thread, "subject": record["subject"], "message_id": message_id}))
    else:
        direction = "you -> agent" if args.as_human else "agent -> you"
        print(f"sent [{direction}] {record['subject']}  (thread: {thread})")


def cmd_poll(args, settings):
    session = resolve_session(args.session)
    human, agent, _ = addresses(settings, session)
    mailbox = human if args.as_human else agent
    query = f"to:{mailbox}"
    if not args.all:
        query += " is:unread"
    result = api(settings, "/api/v1/search", params={"query": query, "limit": args.limit})
    messages = result.get("messages", [])
    if args.thread:
        messages = [m for m in messages if _thread_of(settings, session, m) == args.thread]
    if args.json:
        print(json.dumps([_summary(m) for m in messages], indent=2))
        return
    if not messages:
        print(f"nothing waiting for {mailbox}")
        return
    for m in messages:
        flag = " " if m["Read"] else "*"
        print(f"{flag} {m['ID']}  {m['Subject']}")
        print(f"    from {m['From']['Address']}  {m['Created'][:19]}  {m['Snippet'][:70]}")


def _summary(m):
    return {
        "id": m["ID"],
        "subject": m["Subject"],
        "from": m["From"]["Address"],
        "to": [t["Address"] for t in m.get("To") or []],
        "created": m["Created"],
        "read": m["Read"],
        "snippet": m["Snippet"],
    }


def _thread_of(settings, session, message):
    for record in list_threads(settings, session):
        if record["subject"] == message["Subject"]:
            return record["thread"]
    return None


def cmd_read(args, settings):
    message = api(settings, f"/api/v1/message/{args.id}")
    if not args.keep_unread:
        api(settings, "/api/v1/messages", method="PUT", payload={"IDs": [args.id], "Read": True})
    if args.json:
        print(json.dumps(message, indent=2))
        return
    print(f"Subject: {message['Subject']}")
    print(f"From:    {message['From']['Address']}")
    print(f"To:      {', '.join(t['Address'] for t in message.get('To') or [])}")
    print(f"Date:    {message.get('Date', '')}")
    print()
    print(message.get("Text") or re.sub(r"<[^>]+>", "", message.get("HTML") or ""))


def cmd_threads(args, settings):
    session = resolve_session(args.session)
    records = list_threads(settings, session)
    if args.json:
        print(json.dumps(records, indent=2))
        return
    if not records:
        print(f"no threads yet for session {session[:8]}")
        return
    for r in records:
        print(f"{r['thread']:<30} {len(r['message_ids']):>3} msg  {r.get('updated', '')[:19]}")
        print(f"{'':<30} {r['subject']}")


def cmd_history(args, settings):
    session = resolve_session(args.session)
    record = load_thread(settings, session, args.thread)
    if record is None:
        sys.exit(f"no thread '{args.thread}' for session {session[:8]}")
    entries = list(reversed(record.get("messages", [])))
    if args.json:
        print(json.dumps({**record, "messages": entries}, indent=2))
        return
    print(f"{record['subject']}  ({len(entries)} messages, newest first)")
    for entry in entries:
        body = entry.get("text") or re.sub(r"<[^>]+>", " ", entry.get("html") or "")
        print(f"\n  {entry['author']:<6} {entry['sent_at']}")
        print(f"         {' '.join(body.split())[:100]}")


def cmd_status(args, settings):
    session = args.session or os.environ.get("AIMEL_SESSION") or detect_session()
    human, agent, _ = addresses(settings, session or "unknown0")
    info = api(settings, "/api/v1/info")
    counts = api(settings, "/api/v1/messages", params={"limit": 1})
    print(f"mailpit    {info.get('Version')} at {settings['api_base']}  ({counts.get('total', 0)} messages)")
    print(f"database   {mail_dir(settings)}")
    print(f"session    {session or '(undetected — pass --session)'}")
    print(f"you        {human}")
    print(f"agent      {agent}")
    print(f"subject    {settings['subject_template']}")
    print(f"settings   {SETTINGS_PATH}")


def cmd_settings(args, settings):
    if args.set:
        for pair in args.set:
            key, _, value = pair.partition("=")
            if key not in DEFAULTS:
                sys.exit(f"unknown setting '{key}' — known: {', '.join(sorted(DEFAULTS))}")
            settings[key] = value
        save_settings(settings)
    print(json.dumps(settings, indent=2, sort_keys=True))


# --- entrypoint ---

def main(argv=None):
    parser = argparse.ArgumentParser(prog="aimel", description=__doc__)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--session", help="session uuid (default: newest Claude transcript)")
    common.add_argument("--json", action="store_true", help="machine-readable output")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=lambda **kw:
                               argparse.ArgumentParser(parents=[common], **kw))

    send = sub.add_parser("send", help="open or continue a thread (agent -> you)")
    send.add_argument("--thread", help="thread slug; derived from --title when omitted")
    send.add_argument("--title", help="human-readable thread title, required to open a thread")
    send.add_argument("--html")
    send.add_argument("--text")
    send.add_argument("--as-human", action="store_true", help="send as you, to the agent")
    send.add_argument("--no-history", action="store_true", help="omit the quoted thread history")
    send.set_defaults(func=cmd_send)

    say = sub.add_parser("say", help="reply to an agent (you -> agent)")
    say.add_argument("--thread", required=True)
    say.add_argument("--title")
    say.add_argument("--html")
    say.add_argument("--text")
    say.add_argument("--no-history", action="store_true")
    say.set_defaults(func=cmd_send, as_human=True)

    history = sub.add_parser("history", help="thread history, newest first")
    history.add_argument("--thread", required=True)
    history.set_defaults(func=cmd_history)

    poll = sub.add_parser("poll", help="list mail waiting for this session")
    poll.add_argument("--thread")
    poll.add_argument("--all", action="store_true", help="include already-read mail")
    poll.add_argument("--as-human", action="store_true", help="poll your mailbox instead")
    poll.add_argument("--limit", type=int, default=50)
    poll.set_defaults(func=cmd_poll)

    read = sub.add_parser("read", help="print a message and mark it read")
    read.add_argument("id")
    read.add_argument("--keep-unread", action="store_true")
    read.set_defaults(func=cmd_read)

    threads = sub.add_parser("threads", help="list threads for this session")
    threads.set_defaults(func=cmd_threads)

    status = sub.add_parser("status", help="show resolved config and mailpit health")
    status.set_defaults(func=cmd_status)

    conf = sub.add_parser("settings", help="show or change saved settings")
    conf.add_argument("--set", action="append", metavar="KEY=VALUE")
    conf.set_defaults(func=cmd_settings)

    args = parser.parse_args(argv)
    if not hasattr(args, "as_human"):
        args.as_human = False
    return args.func(args, load_settings())


if __name__ == "__main__":
    main()
