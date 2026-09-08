"""The browser-facing adapter: renders threads and accepts replies.

Mailpit can only view captured mail, so replying needs a surface of our own. Threads collapse here,
which the flat capture list could never do.
"""

from __future__ import annotations

from html import escape

from adapters.resource.requests import ReplyRequest
from common.naming import NamingPolicy
from common.session import SessionDetector
from common.session_color import SessionColorPalette
from core.inbox_service import InboxService
from domain.commands import IncludeHistory
from domain.message import Actor, Message, SessionId

STYLE = """
:root { color-scheme: light dark; }
body { font: 15px/1.5 -apple-system, system-ui, sans-serif; margin: 0; padding: 2rem;
       max-width: 52rem; }
a { color: inherit; }
h1 { font-size: 1.1rem; letter-spacing: .04em; text-transform: uppercase; opacity: .55;
     margin: 0 0 1.5rem; }
.thread { display: block; text-decoration: none; padding: .9rem 0;
          border-bottom: 1px solid color-mix(in oklab, currentColor 15%, transparent); }
.thread:hover { background: color-mix(in oklab, currentColor 5%, transparent); }
.subject { font-weight: 600; }
.meta { font-size: .82rem; opacity: .6; }
.chip { font-family: ui-monospace, monospace; font-size: .78rem; padding: .1rem .4rem;
        border-radius: .35rem; color: #111; }
.email { border-left: 3px solid color-mix(in oklab, currentColor 20%, transparent);
         padding: .2rem 0 .2rem 1rem; margin: 1.4rem 0; }
.email.human { border-left-color: #44BB99; }
.who { font-size: .8rem; opacity: .6; margin-bottom: .3rem; }
.body details { margin-top: .8rem; opacity: .75; }
textarea { width: 100%; min-height: 7rem; font: inherit; padding: .7rem; border-radius: .4rem;
           border: 1px solid color-mix(in oklab, currentColor 25%, transparent);
           background: transparent; color: inherit; }
button { margin-top: .6rem; font: inherit; padding: .5rem 1.1rem; border-radius: .4rem;
         border: 1px solid color-mix(in oklab, currentColor 30%, transparent);
         background: transparent; color: inherit; cursor: pointer; }
button:hover { background: color-mix(in oklab, currentColor 10%, transparent); }
.hint { font-size: .8rem; opacity: .55; margin-top: .4rem; }
"""


class EmailWebResource:
    def __init__(
        self,
        inbox_service: InboxService,
        naming_policy: NamingPolicy,
        session_detector: SessionDetector,
        session_colors: SessionColorPalette,
    ):
        self._inbox = inbox_service
        self._naming = naming_policy
        self._sessions = session_detector
        self._colors = session_colors

    # --- pages ---

    def threads_page(self) -> str:
        session = self._sessions.resolve()
        threads = self._inbox.threads(SessionId(str(session)))
        if not threads:
            return self._page("Inbox", "<p class=meta>No mail yet.</p>")
        rows = []
        for thread in threads:
            rows.append(
                f'<a class=thread href="/email/{thread.latest_email_id}">'
                f'<div class=subject>{escape(thread.subject.text)}</div>'
                f"<div class=meta>{self._chip(thread.session)} "
                f"{thread.message_count} email(s) · "
                f"{thread.updated_at.strftime('%b %-d, %H:%M')}</div></a>"
            )
        return self._page("Inbox", "".join(rows))

    def thread_page(self, email_id: str) -> str:
        history = self._inbox.history(email_id)
        if not history:
            return self._page("Not found", "<p class=meta>No such email.</p>")
        subject = history[-1].content.subject.text
        body = "".join(self._email_block(message) for message in history)
        newest = history[0].content.id
        form = (
            f'<form method=post action="/email/{newest}/reply">'
            "<textarea name=html placeholder=\"Your reply. HTML works: <p>, <ul>, <pre>.\""
            " autofocus></textarea>"
            "<div><button type=submit>Reply</button></div>"
            "<div class=hint>Sends as you, to the agent, on this thread.</div>"
            "</form>"
        )
        return self._page(
            subject,
            f'<p class=meta><a href="/">&larr; all threads</a></p>{body}{form}',
        )

    # --- actions ---

    def reply(self, email_id: str, markup: str) -> str:
        """Returns the id of the email just sent, for the redirect."""
        session = self._sessions.resolve()
        human = self._naming.human_address(SessionId(str(session)))
        agent = self._naming.agent_address(SessionId(str(session)))
        request = ReplyRequest(
            session=str(session),
            email_id=email_id,
            html=markup,
            actor=Actor.HUMAN,
            include_history=IncludeHistory.ALL,
        )
        sent = self._inbox.reply(request.to_domain(SessionId(str(session)), human, agent))
        return sent.content.id

    # --- rendering ---

    def _email_block(self, message: Message) -> str:
        content = message.content
        who = "you" if content.author is Actor.HUMAN else "agent"
        css = "human" if content.author is Actor.HUMAN else "agent"
        return (
            f'<div class="email {css}">'
            f"<div class=who>{who} · {content.sent_at.strftime('%b %-d, %H:%M')} · "
            f"{escape(str(content.sender))} &rarr; {escape(str(content.recipient))}</div>"
            f"<div class=body>{content.body_html.markup}</div></div>"
        )

    def _chip(self, session: SessionId) -> str:
        color = self._colors.color_for(session)
        return f'<span class=chip style="background:{color}">{session.short}</span>'

    @staticmethod
    def _page(title: str, body: str) -> str:
        return (
            "<!doctype html><html><head><meta charset=utf-8>"
            '<meta name=viewport content="width=device-width,initial-scale=1">'
            f"<title>{escape(title)}</title><style>{STYLE}</style></head>"
            f"<body><h1>{escape(title)}</h1>{body}</body></html>"
        )

