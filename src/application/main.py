"""Entrypoint. Builds the composition root, marshals argv once, then calls the resource."""

from __future__ import annotations

import argparse
import json
import sys

from adapters.resource.email_cli_resource import EmailCliResource
from adapters.resource.requests import DrainRequest, MessageRequest, PollRequest, SendRequest
from application.module_dependencies.application_module import ApplicationModule
from common.config import DEFAULTS, AppConfig, ConfigLoader
from common.session_color import SessionColorPalette
from domain.message import Message


class CliApplication:
    def __init__(self, config_loader: ConfigLoader | None = None):
        self._config_loader = config_loader or ConfigLoader()

    def run(self, argv: list[str] | None = None) -> int:
        args = self.parser().parse_args(argv)
        if args.command == "settings":
            return self._settings(args)
        config = self._config_loader.load()
        module = ApplicationModule(config)
        try:
            marshaller = module.provide_cli_request_marshaller()
            request = None if args.command == "status" else marshaller.marshal(args)
            return self._dispatch(
                args.command,
                request,
                module.provide_email_cli_resource(),
                module.provide_session_colors(),
                config,
                as_json=args.json,
            )
        finally:
            module.close()

    # --- argv ---

    @staticmethod
    def parser() -> argparse.ArgumentParser:
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

    # --- commands ---

    def _settings(self, args: argparse.Namespace) -> int:
        """Deliberately skips the composition root — bin/aimel calls this before the db exists."""
        settings = self._config_loader.raw()
        for pair in args.set:
            key, _, value = pair.partition("=")
            if key not in DEFAULTS:
                raise SystemExit(f"unknown setting '{key}' — known: {', '.join(sorted(DEFAULTS))}")
            settings[key] = value
        if args.set:
            self._config_loader.save(settings)
        print(json.dumps(settings, indent=2, sort_keys=True))
        return 0

    def _dispatch(
        self,
        command: str,
        request: object,
        resource: EmailCliResource,
        colors: SessionColorPalette,
        config: AppConfig,
        as_json: bool,
    ) -> int:
        if command == "status":
            return self._status(config)

        if command in {"send", "say"}:
            assert isinstance(request, SendRequest)
            content = resource.send(request).content
            if as_json:
                print(json.dumps({"id": content.id, "subject": content.subject.text,
                                  "thread": str(content.thread)}))
            else:
                direction = "you -> agent" if content.author.value == "human" else "agent -> you"
                print(f"sent [{direction}] {content.subject}  (thread: {content.thread})")
            return 0

        if command == "poll":
            assert isinstance(request, PollRequest)
            messages = resource.poll(request)
            if as_json:
                print(json.dumps([self._summary(m) for m in messages], indent=2))
            elif not messages:
                print(f"nothing waiting for {resource.mailbox_for(request)}")
            else:
                for message in messages:
                    self._print_row(message, colors)
            return 0

        if command in {"read", "delete"}:
            assert isinstance(request, MessageRequest)
            message = resource.read(request) if command == "read" else resource.delete(request)
            content = message.content
            if as_json:
                print(json.dumps(self._summary(message), indent=2))
            elif command == "delete":
                print(f"deleted {content.id}  (deleted_at {message.deleted_at.isoformat()})")
            else:
                print(f"Subject: {content.subject}")
                print(f"From:    {content.sender}")
                print(f"To:      {content.recipient}")
                print(f"Date:    {content.sent_at.isoformat(timespec='seconds')}")
                print()
                print(content.body_text or content.preview)
            return 0

        if command == "history":
            messages = resource.history(request)
            if as_json:
                print(json.dumps([self._summary(m) for m in messages], indent=2))
            elif not messages:
                print("no such thread")
            else:
                first = messages[0].content
                chip = colors.paint(first.session, first.session.short)
                print(f"{chip}  {first.subject}  "
                      f"({len(messages)} messages, newest first)")
                for message in messages:
                    print(f"\n  {message.content.author.value:<6} "
                          f"{message.content.sent_at.isoformat(timespec='seconds')}  "
                          f"[{message.state.value}]")
                    print(f"         {message.content.preview[:100]}")
            return 0

        if command == "threads":
            threads = resource.threads(request)
            if as_json:
                print(json.dumps([
                    {"thread": str(t.thread.slug), "thread_uuid": t.thread.thread_id,
                     "subject": t.subject.text, "messages": t.message_count,
                     "updated_at": t.updated_at.isoformat()} for t in threads], indent=2))
            elif not threads:
                print("no threads yet")
            else:
                for thread in threads:
                    chip = colors.paint(thread.session, thread.session.short)
                    print(f"{str(thread.thread.slug):<40} {thread.message_count:>3} msg  "
                          f"{thread.updated_at.isoformat(timespec='seconds')}")
                    print(f"{'':<40} {chip}  {thread.subject}")
            return 0

        if command == "deleted":
            messages = resource.deleted(request)
            if as_json:
                print(json.dumps([self._summary(m) for m in messages], indent=2))
            elif not messages:
                print("nothing deleted")
            else:
                for message in messages:
                    print(f"  {message.content.id}  {message.content.subject}")
                    print(f"    deleted_at {message.deleted_at.isoformat(timespec='seconds')}"
                          f"  was {message.previous_state.value}")
            return 0

        if command == "drain":
            assert isinstance(request, DrainRequest)
            purge = request.purge or config.purge_after_drain
            claimed = resource.drain(DrainRequest(purge=purge, limit=request.limit))
            print(f"claimed {len(claimed)} message(s) from the intake spool"
                  f"{' and purged it' if purge else ''}")
            return 0

        raise SystemExit(f"unhandled command {command}")

    @staticmethod
    def _status(config: AppConfig) -> int:
        print(f"database   {config.database.path}")
        print(f"smtp       {config.smtp.host}:{config.smtp.port}")
        print(f"spool      {config.mailbox.api_base}")
        print(f"service    {config.naming.service_name}")
        print(f"purge      {config.purge_after_drain}")
        return 0

    # --- output ---

    @staticmethod
    def _summary(message: Message) -> dict:
        content = message.content
        return {
            "id": content.id,
            "state": message.state.value,
            "subject": content.subject.text,
            "from": content.sender.address,
            "to": content.recipient.address,
            "thread": str(content.thread),
            "sent_at": content.sent_at.isoformat(timespec="seconds"),
            "created_at": content.created_at.isoformat(timespec="seconds"),
            "preview": content.preview,
        }

    @staticmethod
    def _print_row(message: Message, colors: SessionColorPalette) -> None:
        content = message.content
        chip = colors.paint(content.session, content.session.short)
        print(f"* {content.id}  {chip}  {content.subject}")
        print(f"    from {content.sender}  "
              f"{content.sent_at.isoformat(timespec='seconds')}  {content.preview[:70]}")


def main(argv: list[str] | None = None) -> int:
    return CliApplication().run(argv)


if __name__ == "__main__":
    sys.exit(main())
