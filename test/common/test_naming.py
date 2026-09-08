from __future__ import annotations

import unittest

from common.config import NamingConfig
from common.naming import NamingPolicy


def policy(human_address: str) -> NamingPolicy:
    return NamingPolicy(
        NamingConfig(
            service_name="aimel",
            domain="aimel.com",
            user="someone",
            human_address=human_address,
            agent_address="claude-{session8}@{domain}",
            subject_template="{title}",
        )
    )


class MailboxOwnerAddressTest(unittest.TestCase):
    """An inbox listing belongs to no session, so it must not have to invent one."""

    def test_resolves_when_the_template_does_not_depend_on_a_session(self) -> None:
        self.assertEqual(
            policy("{user}@{domain}").mailbox_owner_address().address, "someone@aimel.com"
        )

    def test_raises_rather_than_guessing_when_the_template_needs_a_session(self) -> None:
        with self.assertRaises(ValueError) as caught:
            policy("{user}-{session8}@{domain}").mailbox_owner_address()

        self.assertIn("session8", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
