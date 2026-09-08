from __future__ import annotations

import argparse

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
from domain.commands import IncludeHistory
from domain.message import Actor


def _actor(as_human: bool) -> Actor:
    return Actor.HUMAN if as_human else Actor.AI_AGENT


def _history(no_history: bool) -> IncludeHistory:
    return IncludeHistory.NONE if no_history else IncludeHistory.ALL


BUILDERS = {
    "send": lambda a: SendNewThreadRequest(
        session=a.session, title=a.title, html=a.html, text=a.text, actor=_actor(a.as_human)
    ),
    "reply": lambda a: ReplyRequest(
        session=a.session,
        email_id=a.email_id,
        html=a.html,
        text=a.text,
        actor=Actor.AI_AGENT,
        include_history=_history(a.no_history),
    ),
    "say": lambda a: ReplyRequest(
        session=a.session,
        email_id=a.email_id,
        html=a.html,
        text=a.text,
        actor=Actor.HUMAN,
        include_history=_history(a.no_history),
    ),
    "delete": lambda a: DeleteRequest(email_id=a.email_id),
    "read": lambda a: EmailIdRequest(email_id=a.email_id),
    "history": lambda a: EmailIdRequest(email_id=a.email_id),
    "poll": lambda a: PollRequest(
        session=a.session, mailbox_owner=_actor(a.as_human), limit=a.limit
    ),
    "threads": lambda a: SessionScopedRequest(session=a.session),
    "deleted": lambda a: ListRequest(limit=50),
    "drain": lambda a: DrainRequest(purge=a.purge, limit=a.limit),
}


class CliRequestMarshaller:
    """Turns argv into a validated request at the edge, before any logic runs."""

    def marshal(self, args: argparse.Namespace):
        builder = BUILDERS.get(args.command)
        if builder is None:
            raise SystemExit(f"nothing to marshal for {args.command}")
        return builder(args)
