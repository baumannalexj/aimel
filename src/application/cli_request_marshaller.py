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

BUILDERS = {
    "send": lambda a: SendNewThreadRequest(
        session=a.session, title=a.title, html=a.html, text=a.text, as_human=a.as_human
    ),
    "reply": lambda a: ReplyRequest(
        session=a.session,
        email_id=a.email_id,
        html=a.html,
        text=a.text,
        as_human=False,
        include_history=not a.no_history,
    ),
    "say": lambda a: ReplyRequest(
        session=a.session,
        email_id=a.email_id,
        html=a.html,
        text=a.text,
        as_human=True,
        include_history=not a.no_history,
    ),
    "delete": lambda a: DeleteRequest(email_id=a.email_id),
    "read": lambda a: EmailIdRequest(email_id=a.email_id),
    "history": lambda a: EmailIdRequest(email_id=a.email_id),
    "poll": lambda a: PollRequest(session=a.session, as_human=a.as_human, limit=a.limit),
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
