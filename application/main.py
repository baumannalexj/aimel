"""Entrypoint. Builds the composition root, then hands argv to the upstream adapter."""

from __future__ import annotations

import argparse
import json
import sys

from adapters.resource.email_cli_resource import (
    EmailCliResource,
    MessageRequest,
    PollRequest,
    SendRequest,
    ThreadRequest,
)
from application.module_dependencies.application_module import ApplicationModule
from common import config as config_loader
from common.session import detect
from domain.message import Message


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aimel")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--session", default="")
    common.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(
        dest="command",
        required=True,
        parser_class=lambda **kw: argparse.ArgumentParser(parents=[common], **kw),
    )

    for name, help_text in (("send", "open or continue a thread"), ("say", "reply as you")):
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("--thread", default="")
        cmd.add_argument("--title", default="")
        cmd.add_argument("--html", default="")
        cmd.add_argument("--text", default="")
        cmd.add_argument("--no-history", action="store_true")
        if name == "send":
            cmd.add_argument("--as-human", action="store_true")

    poll = sub.add_parser("poll", help="unread mail for this session")
    poll.add_argument("--thread", default="")
    poll.add_argument("--as-human", action="store_true")
    poll.add_argument("--limit", type=int, default=50)

    for name, help_text in (("read", "read a message"), ("delete", "soft delete a message")):
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("id")

    history = sub.add_parser("history", help="thread history, newest first")
    history.add_argument("--thread", required=True)

    sub.add_parser("threads", help="threads for this session")
    sub.add_parser("deleted", help="soft-deleted mail")
    sub.add_parser("status", help="resolved config and health")

    settings = sub.add_parser("settings", help="show or change saved settings")
    settings.add_argument("--set", action="append", metavar="KEY=VALUE", default=[])

    drain = sub.add_parser("drain", help="take ownership of intake-spool mail")
    drain.add_argument("--purge", action="store_true")
    drain.add_argument("--limit", type=int, default=200)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "settings":
        return run_settings(args)
    config = config_loader.load()
    module = ApplicationModule(config)
    resource = EmailCliResource(module.provide_inbox_service(), config.naming)
    try:
        return dispatch(args, resource, module, config)
    finally:
        module.close()


def run_settings(args) -> int:
    """Deliberately avoids the composition root — bin/aimel calls this before the db exists."""
    settings = config_loader.raw_settings()
    if args.set:
        for pair in args.set:
            key, _, value = pair.partition("=")
            if key not in config_loader.DEFAULTS:
                raise SystemExit(
                    f"unknown setting '{key}' — known: {', '.join(sorted(config_loader.DEFAULTS))}"
                )
            settings[key] = value
        config_loader.save_settings(settings)
    print(json.dumps(settings, indent=2, sort_keys=True))
    return 0


def dispatch(args, resource: EmailCliResource, module: ApplicationModule, config) -> int:
    if args.command in {"send", "say"}:
        message = resource.send(
            SendRequest(
                session=args.session,
                thread=args.thread,
                title=args.title,
                html=args.html,
                text=args.text,
                as_human=args.command == "say" or getattr(args, "as_human", False),
                include_history=not args.no_history,
            )
        )
        content = message.content
        if args.json:
            print(json.dumps({"id": content.id, "subject": content.subject,
                              "thread": str(content.thread)}))
        else:
            direction = "you -> agent" if content.author.value == "human" else "agent -> you"
            print(f"sent [{direction}] {content.subject}  (thread: {content.thread})")
        return 0

    if args.command == "poll":
        messages = resource.poll(
            PollRequest(
                session=args.session,
                thread=args.thread,
                as_human=args.as_human,
                limit=args.limit,
            )
        )
        if args.json:
            print(json.dumps([_summary(m) for m in messages], indent=2))
        elif not messages:
            print(f"nothing waiting for {resource.mailbox_for(args.session, args.as_human)}")
        else:
            for message in messages:
                _print_row(message)
        return 0

    if args.command in {"read", "delete"}:
        request = MessageRequest(message_id=args.id)
        message = resource.read(request) if args.command == "read" else resource.delete(request)
        content = message.content
        if args.json:
            print(json.dumps(_summary(message), indent=2))
        elif args.command == "delete":
            print(f"deleted {content.id}  (deleted_at {message.deleted_at.isoformat()})")
        else:
            print(f"Subject: {content.subject}")
            print(f"From:    {content.sender}")
            print(f"To:      {content.recipient}")
            print(f"Date:    {content.sent_at.isoformat(timespec='seconds')}")
            print()
            print(content.body_text or content.preview)
        return 0

    if args.command == "history":
        messages = resource.history(ThreadRequest(session=args.session, thread=args.thread))
        if args.json:
            print(json.dumps([_summary(m) for m in messages], indent=2))
        elif not messages:
            print(f"no thread '{args.thread}'")
        else:
            print(f"{messages[0].content.subject}  ({len(messages)} messages, newest first)")
            for message in messages:
                print(f"\n  {message.content.author.value:<6} "
                      f"{message.content.sent_at.isoformat(timespec='seconds')}  "
                      f"[{message.state.value}]")
                print(f"         {message.content.preview[:100]}")
        return 0

    if args.command == "threads":
        threads = resource.threads(args.session)
        if args.json:
            print(json.dumps([
                {"thread": str(t.slug), "subject": t.subject, "messages": t.message_count,
                 "updated_at": t.updated_at.isoformat()} for t in threads], indent=2))
        elif not threads:
            print("no threads yet")
        else:
            for thread in threads:
                print(f"{str(thread.slug):<40} {thread.message_count:>3} msg  "
                      f"{thread.updated_at.isoformat(timespec='seconds')}")
                print(f"{'':<40} {thread.subject}")
        return 0

    if args.command == "deleted":
        messages = resource.deleted()
        if args.json:
            print(json.dumps([_summary(m) for m in messages], indent=2))
        elif not messages:
            print("nothing deleted")
        else:
            for message in messages:
                print(f"  {message.content.id}  {message.content.subject}")
                print(f"    deleted_at {message.deleted_at.isoformat(timespec='seconds')}")
        return 0

    if args.command == "drain":
        purge = args.purge or config.purge_after_drain
        claimed = resource.drain(purge=purge, limit=args.limit)
        print(f"claimed {len(claimed)} message(s) from the intake spool"
              f"{' and purged it' if purge else ''}")
        return 0

    if args.command == "status":
        print(f"database   {config.database.path}")
        print(f"session    {detect() or '(undetected)'}")
        print(f"smtp       {config.smtp.host}:{config.smtp.port}")
        print(f"spool      {config.mailbox.api_base}")
        print(f"service    {config.naming.service_name}")
        print(f"purge      {config.purge_after_drain}")
        return 0

    raise SystemExit(f"unhandled command {args.command}")


def _summary(message: Message) -> dict:
    content = message.content
    return {
        "id": content.id,
        "state": message.state.value,
        "subject": content.subject,
        "from": str(content.sender),
        "to": str(content.recipient),
        "thread": str(content.thread),
        "sent_at": content.sent_at.isoformat(timespec="seconds"),
        "preview": content.preview,
    }


def _print_row(message: Message) -> None:
    content = message.content
    print(f"* {content.id}  {content.subject}")
    print(f"    from {content.sender}  "
          f"{content.sent_at.isoformat(timespec='seconds')}  {content.preview[:70]}")


if __name__ == "__main__":
    sys.exit(main())
