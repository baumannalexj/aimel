from __future__ import annotations

import unittest
from unittest.mock import create_autospec

from adapters.resource.email_web_resource import EmailWebResource
from common.config import NamingConfig
from common.feature_flag_service import EmailRespondFlag, FeatureFlagService, FlagState
from common.naming import NamingPolicy
from common.session import SessionDetector
from common.session_color import SessionColorPalette
from core.inbox_service import InboxService
from domain.message import SessionId
from test.fixtures.correspondence_fixtures import SESSION, CorrespondenceFixtures

NAMING = NamingConfig(
    service_name="aimel",
    domain="aimel.com",
    user="someone",
    human_address="{user}@{domain}",
    agent_address="claude-{session8}@{domain}",
    subject_template="{title}",
)


def build(flags: FeatureFlagService) -> tuple[EmailWebResource, object]:
    inbox = create_autospec(InboxService, spec_set=True, instance=True)
    inbox.history.return_value = [CorrespondenceFixtures.unread_message()]
    sessions = create_autospec(SessionDetector, spec_set=True, instance=True)
    sessions.resolve.return_value = SessionId(SESSION)
    resource = EmailWebResource(
        inbox, NamingPolicy(NAMING), sessions, SessionColorPalette(), feature_flags=flags
    )
    return resource, inbox


class EmailRespondGateTest(unittest.TestCase):
    def test_the_reply_form_is_rendered_when_the_flag_is_on(self) -> None:
        resource, _ = build(FeatureFlagService.with_defaults(environ={}))

        page = resource.thread_page("any-email-id")

        self.assertIn("<form", page)
        self.assertIn("textarea", page)

    def test_the_form_is_withheld_when_the_flag_is_off(self) -> None:
        disabled = FeatureFlagService({EmailRespondFlag.KEY: EmailRespondFlag(FlagState.DISABLED)})
        resource, _ = build(disabled)

        page = resource.thread_page("any-email-id")

        self.assertNotIn("<form", page)
        # The thread itself still reads fine; only responding is gated.
        self.assertIn('class="email', page)

    def test_posting_a_reply_is_refused_when_the_flag_is_off_not_just_hidden(self) -> None:
        disabled = FeatureFlagService({EmailRespondFlag.KEY: EmailRespondFlag(FlagState.DISABLED)})
        resource, inbox = build(disabled)

        with self.assertRaises(PermissionError):
            resource.reply("any-email-id", "<p>nope</p>")

        inbox.reply.assert_not_called()


if __name__ == "__main__":
    unittest.main()
