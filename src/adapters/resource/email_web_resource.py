"""The browser-facing adapter: renders threads and accepts replies.

Mailpit can only view captured mail, so replying needs a surface of our own. Threads collapse here,
which the flat capture list could never do.

This builds no markup. It maps domain models to props dataclasses and hands them to the renderer;
all HTML and CSS lives in web/templates, and autoescaping means nothing here escapes by hand.
"""

from __future__ import annotations

from markupsafe import Markup

from adapters.resource.requests import ReplyRequest
from common.feature_flag_service import EmailRespondFlag, FeatureFlagService
from common.naming import NamingPolicy
from common.session import SessionDetector
from common.session_color import SessionColorPalette
from core.inbox_service import InboxService
from domain.commands import IncludeHistory
from domain.message import Actor, Message, SessionId
from domain.thread import ThreadSummary
from web.props import (
    ChipProps,
    EmailProps,
    InboxPageProps,
    NoticePageProps,
    ThreadPageProps,
    ThreadRowProps,
)
from web.renderer import HtmlRenderer

WHEN = "%b %-d, %H:%M"


class EmailWebResource:
    def __init__(
        self,
        inbox_service: InboxService,
        naming_policy: NamingPolicy,
        session_detector: SessionDetector,
        session_colors: SessionColorPalette,
        feature_flags: FeatureFlagService | None = None,
        renderer: HtmlRenderer | None = None,
    ):
        self._inbox = inbox_service
        self._naming = naming_policy
        self._sessions = session_detector
        self._colors = session_colors
        self._flags = feature_flags or FeatureFlagService.with_defaults()
        self._renderer = renderer or HtmlRenderer()

    # --- pages ---

    def threads_page(self) -> str:
        # Every session, not just the local one — otherwise other agents' mail is invisible.
        threads = self._inbox.all_threads()
        return self._renderer.page(
            "inbox",
            InboxPageProps(
                title="Inbox",
                rows=tuple(self._thread_row(thread) for thread in threads),
            ),
        )

    def thread_page(self, email_id: str) -> str:
        history = self._inbox.history(email_id)
        if not history:
            return self._renderer.page(
                "notice", NoticePageProps(title="Not found", message="No such email.")
            )
        return self._renderer.page(
            "thread",
            ThreadPageProps(
                title=history[-1].content.subject.text,
                emails=tuple(self._email(message) for message in history),
                newest_email_id=history[0].content.id,
                responding_enabled=self.responding_enabled,
            ),
        )

    # --- actions ---

    def reply(self, email_id: str, markup: str) -> str:
        """Returns the id of the email just sent, for the redirect.

        Addressed from the answered email's session, not the locally detected one. Replying to
        another agent while resolving the local session would post to our own mailbox, and the
        agent that asked would never see the answer.
        """
        self._require_responding_enabled()
        session = self._session_of(email_id)
        request = ReplyRequest(
            session=str(session),
            email_id=email_id,
            html=markup,
            actor=Actor.HUMAN,
            include_history=IncludeHistory.ALL,
        )
        sent = self._inbox.reply(
            request.to_domain(
                session,
                self._naming.human_address(session),
                self._naming.agent_address(session),
            )
        )
        return sent.content.id

    def _session_of(self, email_id: str) -> SessionId:
        history = self._inbox.history(email_id)
        if not history:
            raise ValueError(f"no such email: {email_id}")
        return history[0].content.session

    @property
    def responding_enabled(self) -> bool:
        return self._flags.is_enabled(EmailRespondFlag.KEY)

    def _require_responding_enabled(self) -> None:
        """Hiding the form is not enough — a POST can still arrive."""
        if not self.responding_enabled:
            raise PermissionError(f"{EmailRespondFlag.KEY} is disabled")

    # --- domain to props ---

    def _thread_row(self, thread: ThreadSummary) -> ThreadRowProps:
        return ThreadRowProps(
            latest_email_id=thread.latest_email_id,
            subject=thread.subject.text,
            email_count=thread.message_count,
            updated_at=thread.updated_at.strftime(WHEN),
            chip=ChipProps(
                label=thread.session.short, color=self._colors.color_for(thread.session)
            ),
        )

    def _email(self, message: Message) -> EmailProps:
        content = message.content
        human = content.author is Actor.HUMAN
        return EmailProps(
            css_class="human" if human else "agent",
            who="you" if human else "agent",
            sent_at=content.sent_at.strftime(WHEN),
            sender=str(content.sender),
            recipient=str(content.recipient),
            # Our own markup, so it is trusted; everything else on this page is escaped.
            body=Markup(content.body_html.markup),
        )
