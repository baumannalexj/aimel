from __future__ import annotations

import argparse

from adapters.resource.requests import (
    DrainRequest,
    ListRequest,
    MessageRequest,
    PollRequest,
    SendRequest,
    SessionRequest,
    ThreadRequest,
)
from common.session import SessionDetector
from domain.message import Author, ThreadSlug


class CliRequestMarshaller:
    """Turns argv into typed requests at the edge, before any logic runs."""

    def __init__(self, session_detector: SessionDetector):
        self._sessions = session_detector

    def marshal(self, args: argparse.Namespace) -> object:
        command = args.command
        if command in {"send", "say"}:
            return self._send(args)
        if command == "poll":
            return PollRequest(
                session=self._sessions.resolve(args.session),
                thread=ThreadSlug(args.thread) if args.thread else None,
                mailbox_owner=Author.HUMAN if args.as_human else Author.AGENT,
                limit=args.limit,
            )
        if command in {"read", "delete"}:
            return MessageRequest(message_id=args.id)
        if command == "history":
            return ThreadRequest(
                session=self._sessions.resolve(args.session),
                thread=ThreadSlug(args.thread),
            )
        if command == "threads":
            return SessionRequest(session=self._sessions.resolve(args.session))
        if command == "deleted":
            return ListRequest(limit=50)
        if command == "drain":
            return DrainRequest(purge=args.purge, limit=args.limit)
        raise SystemExit(f"nothing to marshal for {command}")

    def _send(self, args: argparse.Namespace) -> SendRequest:
        if args.thread:
            thread = ThreadSlug(args.thread)
        elif args.title:
            thread = ThreadSlug.from_title(args.title)
        else:
            raise ValueError("pass --thread or --title so the correspondence has a thread")
        as_human = args.command == "say" or getattr(args, "as_human", False)
        return SendRequest(
            session=self._sessions.resolve(args.session),
            thread=thread,
            title=args.title,
            html=args.html,
            text=args.text,
            author=Author.HUMAN if as_human else Author.AGENT,
            include_history=not args.no_history,
        )
