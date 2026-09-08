"""Entrypoint. Builds the composition root, marshals argv once, then calls the resource."""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

from pydantic import ValidationError

from adapters.resource.email_cli_resource import EmailCliResource
from adapters.resource.responses import EmailDeletedResponse, EmailSentResponse
from application.module_dependencies.application_module import ApplicationModule
from application.api_server import ApiServer
from application.web_server import WebServer
from common.config import AppConfig, AppSettings, ConfigLoader
from common.session_color import SessionColorPalette
from domain.message import Message


class CliApplication:
    def __init__(self, config_loader: ConfigLoader | None = None):
        self._config_loader = config_loader or ConfigLoader()

    def run(self, argv: list[str] | None = None) -> int:
        args = self.parser().parse_args(argv)
        if args.command == "settings":
            return self._settings(args)
        if args.command == "up":
            # Chosen and saved before the composition root reads config, so the db path is right.
            self._choose_mail_dir()
        config = self._config_loader.load()
        module = ApplicationModule(config)
        try:
            if args.command in {"up", "down", "restart", "logs"}:
                return self._lifecycle(args, module, config)
            if args.command == "install-skill":
                print(f"installed skill -> {module.provide_skill_installer().install()}")
                return 0
            if args.command == "open":
                webbrowser.open(config.mailbox.api_base)
                return 0
            if args.command == "status":
                return self._status(config)
            if args.command == "api":
                server = ApiServer(
                    module.provide_email_api_resource(),
                    module.provide_session_directory_resource(),
                    host=args.host,
                    port=args.port or config.web.api_port,
                )
                print(f"api on {server.url}  (ctrl-c to stop)")
                server.serve_forever()
                return 0
            if args.command == "serve":
                server = WebServer(
                    module.provide_email_web_resource(),
                    host=args.host,
                    port=args.port or config.web.reply_port,
                )
                print(f"reply to your agents at {server.url}  (ctrl-c to stop)")
                server.serve_forever()
                return 0
            request = module.provide_cli_request_marshaller().marshal(args)
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

        send = sub.add_parser("send", help="open a new thread")
        send.add_argument("--title", required=True, help="the thread's subject, set once")
        send.add_argument("--html", default="")
        send.add_argument("--text", default="")
        send.add_argument("--as-human", action="store_true")

        for name, help_text in (
            ("reply", "reply to an email as the agent"),
            ("say", "reply to an email as you"),
        ):
            cmd = sub.add_parser(name, help=help_text)
            cmd.add_argument("email_id", help="the email being answered")
            cmd.add_argument("--html", default="")
            cmd.add_argument("--text", default="")
            cmd.add_argument("--no-history", action="store_true")

        for name, help_text in (
            ("read", "read an email"),
            ("delete", "soft delete an email"),
            ("history", "the thread containing an email, newest first"),
        ):
            cmd = sub.add_parser(name, help=help_text)
            cmd.add_argument("email_id")

        poll = sub.add_parser("poll", help="unread mail for this session")
        poll.add_argument("--as-human", action="store_true")
        poll.add_argument("--limit", type=int, default=50)

        sub.add_parser("up", help="start the intake spool")
        sub.add_parser("down", help="stop it; mail survives in the database")
        sub.add_parser("restart", help="bounce it")
        logs = sub.add_parser("logs", help="spool logs")
        logs.add_argument("-f", "--follow", action="store_true")
        sub.add_parser("install-skill", help="copy the agent contract into ~/.claude/skills")
        sub.add_parser("open", help="open the spool viewer in a browser")

        sub.add_parser("threads", help="threads for this session")
        sub.add_parser("deleted", help="soft-deleted mail")
        sub.add_parser("status", help="resolved config and health")

        api = sub.add_parser("api", help="json api for the web client")
        api.add_argument("--port", type=int, default=None)
        api.add_argument("--host", default="127.0.0.1")

        serve = sub.add_parser("serve", help="the reply-capable web view")
        serve.add_argument("--port", type=int, default=None)
        serve.add_argument("--host", default="127.0.0.1")

        settings = sub.add_parser("settings", help="show or change saved settings")
        settings.add_argument("--set", action="append", metavar="DOTTED.KEY=VALUE", default=[])

        drain = sub.add_parser("drain", help="take ownership of intake-spool mail")
        drain.add_argument("--purge", action="store_true")
        drain.add_argument("--limit", type=int, default=200)

        return parser

    # --- commands ---

    def _settings(self, args: argparse.Namespace) -> int:
        """Deliberately skips the composition root — it must work before the database exists.

        A key is a dotted path into the config shape, e.g. `--set smtpConfig.port=1025`.
        """
        settings = self._config_loader.raw()
        for pair in args.set:
            dotted_key, _, value = pair.partition("=")
            self._set_dotted(settings, dotted_key.split("."), value)
        if args.set:
            try:
                AppSettings.model_validate(settings)
            except ValidationError as exc:
                raise SystemExit(f"invalid setting: {exc}") from exc
            self._config_loader.save(settings)
        print(json.dumps(settings, indent=2, sort_keys=True))
        return 0

    @staticmethod
    def _set_dotted(settings: dict, path: list[str], value: str) -> None:
        node = settings
        for key in path[:-1]:
            node = node.setdefault(key, {})
        node[path[-1]] = value

    def _choose_mail_dir(self) -> None:
        settings = self._config_loader.raw()
        default = str(settings["mailDir"])
        answer = ""
        if sys.stdin.isatty():
            answer = input(f"email database dir [{default}]: ").strip()
        settings["mailDir"] = str(Path(answer or default).expanduser())
        self._config_loader.save(settings)

    def _lifecycle(self, args, module: ApplicationModule, config: AppConfig) -> int:
        runtime = module.provide_container_runtime()
        if args.command == "up":
            runtime.up(config.mail_dir)
            if not runtime.wait_until_ready(f"{config.mailbox.api_base}/api/v1/info"):
                print("the spool did not come up - try: uv run aimel logs", file=sys.stderr)
                return 1
            return self._status(config)
        if args.command == "down":
            runtime.down(config.mail_dir)
            return 0
        if args.command == "restart":
            runtime.restart(config.mail_dir)
            return 0
        return runtime.logs(config.mail_dir, follow=args.follow)

    def _dispatch(
        self,
        command: str,
        request,
        resource: EmailCliResource,
        colors: SessionColorPalette,
        config: AppConfig,
        as_json: bool,
    ) -> int:
        if command in {"send", "reply", "say"}:
            message = (
                resource.send_new_thread(request)
                if command == "send"
                else resource.reply(request)
            )
            response = EmailSentResponse.of(message)
            if as_json:
                print(response.model_dump_json(indent=2))
            else:
                direction = (
                    "you -> agent" if message.content.author.value == "human" else "agent -> you"
                )
                print(f"sent [{direction}] {response.subject}")
                print(f"  email  {response.email_id}")
                print(f"  thread {response.thread_uuid}")
            return 0

        if command == "poll":
            messages = resource.poll(request)
            if as_json:
                print(json.dumps([self._summary(m) for m in messages], indent=2))
            elif not messages:
                print(f"nothing waiting for {resource.mailbox_for(request)}")
            else:
                for message in messages:
                    self._print_row(message, colors)
                print(f"\nreply with: aimel say <email> --html \"<p>…</p>\"")
            return 0

        if command == "read":
            content = resource.read(request).content
            if as_json:
                print(json.dumps(self._summary_of(content), indent=2))
            else:
                print(f"Subject: {content.subject}")
                print(f"From:    {content.sender}")
                print(f"To:      {content.recipient}")
                print(f"Date:    {content.sent_at.isoformat(timespec='seconds')}")
                print(f"Email:   {content.id}")
                print()
                print(content.body_text or content.preview)
            return 0

        if command == "delete":
            response = EmailDeletedResponse.of(resource.delete(request))
            if as_json:
                print(response.model_dump_json(indent=2))
            else:
                print(f"deleted {response.email_id}  ({response.deleted_at}, "
                      f"was {response.previous_state})")
            return 0

        if command == "history":
            messages = resource.history(request)
            if as_json:
                print(json.dumps([self._summary(m) for m in messages], indent=2))
            elif not messages:
                print("no such email")
            else:
                first = messages[0].content
                chip = colors.paint(first.session, first.session.short)
                print(f"{chip}  {first.subject}  ({len(messages)} emails, newest first)")
                for message in messages:
                    print(f"\n  {message.content.author.value:<6} "
                          f"{message.content.sent_at.isoformat(timespec='seconds')}  "
                          f"[{message.state.value}]  {message.content.id}")
                    print(f"         {message.content.preview[:100]}")
            return 0

        if command == "threads":
            threads = resource.threads(request)
            if as_json:
                print(json.dumps([
                    {"thread_uuid": t.thread_uuid, "subject": t.subject.text,
                     "emails": t.message_count, "latest_email_id": t.latest_email_id,
                     "updated_at": t.updated_at.isoformat()} for t in threads], indent=2))
            elif not threads:
                print("no threads yet")
            else:
                for thread in threads:
                    chip = colors.paint(thread.session, thread.session.short)
                    print(f"{chip}  {thread.subject}  ({thread.message_count} emails, "
                          f"{thread.updated_at.isoformat(timespec='seconds')})")
                    print(f"      latest {thread.latest_email_id}")
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
            purge = request.purge or config.purge_after_drain
            claimed = resource.drain(request.model_copy(update={"purge": purge}))
            print(f"claimed {len(claimed)} email(s) from the intake spool"
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

    @classmethod
    def _summary(cls, message: Message) -> dict:
        return {"state": message.state.value} | cls._summary_of(message.content)

    @staticmethod
    def _summary_of(content) -> dict:
        return {
            "id": content.id,
            "thread_uuid": content.thread_uuid,
            "subject": content.subject.text,
            "from": content.sender.address,
            "to": content.recipient.address,
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
