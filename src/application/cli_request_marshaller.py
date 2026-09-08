from __future__ import annotations

import argparse
from uuid import UUID

from adapters.resource.requests import (
    DeleteRequest,
    DrainRequest,
    EmailIdRequest,
    ListRequest,
    PollRequest,
    ReplyRequest,
    SendNewThreadRequest,
    SessionScopedRequest,
)
from common.session import SessionDetector
from domain.commands import IncludeHistory
from domain.message import Actor


def _actor(as_human: bool) -> Actor:
    return Actor.HUMAN if as_human else Actor.AI_AGENT


def _history(no_history: bool) -> IncludeHistory:
    return IncludeHistory.NONE if no_history else IncludeHistory.ALL




class CliRequestMarshaller:
    """Turns argv into a validated request at the edge, before any logic runs.

    The session is resolved here, so requests carry a real uuid rather than an empty-string
    sentinel meaning "work it out later".
    """

    def __init__(self, session_detector: SessionDetector):
        self._sessions = session_detector

    def marshal(self, args: argparse.Namespace):
        builders = {
            "send": lambda: SendNewThreadRequest(
                session=self._session(args), title=args.title, html=args.html,
                actor=_actor(args.as_human),
            ),
            "reply": lambda: ReplyRequest(
                session=self._session(args), email_id=args.email_id, html=args.html,
                actor=Actor.AI_AGENT,
                include_history=_history(args.no_history),
            ),
            "say": lambda: ReplyRequest(
                session=self._session(args), email_id=args.email_id, html=args.html,
                actor=Actor.HUMAN,
                include_history=_history(args.no_history),
            ),
            "delete": lambda: DeleteRequest(email_id=args.email_id),
            "read": lambda: EmailIdRequest(email_id=args.email_id),
            "history": lambda: EmailIdRequest(email_id=args.email_id),
            "poll": lambda: PollRequest(
                session=self._session(args), mailbox_owner=_actor(args.as_human),
                limit=args.limit,
            ),
            "threads": lambda: SessionScopedRequest(session=self._session(args)),
            "deleted": lambda: ListRequest(limit=50),
            "drain": lambda: DrainRequest(purge=args.purge, limit=args.limit),
        }
        builder = builders.get(args.command)
        if builder is None:
            raise SystemExit(f"nothing to marshal for {args.command}")
        return builder()

    def _session(self, args: argparse.Namespace) -> UUID:
        return UUID(str(self._sessions.resolve(args.session)))
