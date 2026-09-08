from __future__ import annotations

import unittest

from adapters.client.mailpit_mailbox_client import MailpitMailboxClient
from adapters.client.smtp_email_transport import SmtpEmailTransport
from common.config import MailboxConfig, SmtpConfig
from common.headers import HttpHeaders, MailHeaders


class MailHeadersTest(unittest.TestCase):
    def test_names_are_derived_from_the_service_name(self) -> None:
        headers = MailHeaders("aimel")

        self.assertEqual(headers.session, "X-Aimel-Session")
        self.assertEqual(headers.actor, "X-Aimel-Actor")
        self.assertEqual(headers.tags, "X-Tags")

    def test_renaming_the_service_moves_every_custom_header_together(self) -> None:
        headers = MailHeaders("postbox")

        self.assertEqual(headers.session, "X-Postbox-Session")
        self.assertEqual(headers.actor, "X-Postbox-Actor")

    def test_the_writer_and_the_reader_agree_on_the_names(self) -> None:
        """The drift this guards: rename the service and intake stops recognising its own mail."""
        transport = SmtpEmailTransport(SmtpConfig(host="h", port=1, service_name="postbox"))
        client = MailpitMailboxClient(MailboxConfig(api_base="http://h"), "postbox")

        self.assertEqual(transport._headers.session, client._headers.session)
        self.assertEqual(transport._headers.actor, client._headers.actor)

    def test_http_header_names_are_shared_too(self) -> None:
        self.assertEqual(HttpHeaders.HTML_UTF8, "text/html; charset=utf-8")


if __name__ == "__main__":
    unittest.main()
