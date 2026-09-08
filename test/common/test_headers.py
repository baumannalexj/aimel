from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from adapters.client.mailpit_mailbox_client import MailpitMailboxClient
from adapters.client.smtp_email_transport import SmtpEmailTransport
from common.config import MailboxConfig, SmtpConfig
from common.headers import HttpHeaders, MailHeaders
from domain.message import Actor, Email, EmailSubject, SessionId
from domain.outgoing import Envelope


class MailHeadersTest(unittest.TestCase):
    def test_mail_header_names(self) -> None:
        self.assertEqual(MailHeaders.SESSION, "X-Aimel-Session")
        self.assertEqual(MailHeaders.THREAD, "X-Aimel-Thread")
        self.assertEqual(MailHeaders.ACTOR, "X-Aimel-Actor")
        self.assertEqual(MailHeaders.TAGS, "X-Tags")
        self.assertEqual(MailHeaders.IN_REPLY_TO, "In-Reply-To")
        self.assertEqual(MailHeaders.REFERENCES, "References")

    def test_the_writer_and_the_reader_agree_on_the_names(self) -> None:
        """The drift this guards: rename the service and intake stops recognising its own mail.

        Sends a real message through SmtpEmailTransport (SMTP itself mocked out) and feeds the
        headers it produced back through MailpitMailboxClient's parsing, as Mailpit's headers API
        would report them. If either side ever hardcoded a different literal, this fails.
        """
        envelope = Envelope(
            sender=Email("agent@aimel.com"),
            recipient=Email("human@aimel.com"),
            subject=EmailSubject("hello"),
            session=SessionId("abc12345-session"),
            actor=Actor.AI_AGENT,
            in_reply_to="",
            references=(),
        )

        with patch("smtplib.SMTP") as smtp_cls:
            transport = SmtpEmailTransport(SmtpConfig(host="h", port=1))
            transport.send(envelope, body_html=None, body_text="hi")
            sent_message = smtp_cls.return_value.__enter__.return_value.send_message.call_args[0][0]

        raw_headers = {name: [value] for name, value in sent_message.items()}
        with patch("urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(
                raw_headers
            ).encode()
            client = MailpitMailboxClient(MailboxConfig(api_base="http://h"))
            parsed = client._call("/api/v1/message/1/headers")

        self.assertEqual(parsed[MailHeaders.SESSION], [str(envelope.session)])
        self.assertEqual(parsed[MailHeaders.ACTOR], [envelope.actor.value])

    def test_http_header_names_are_shared_too(self) -> None:
        self.assertEqual(HttpHeaders.HTML_UTF8, "text/html; charset=utf-8")


if __name__ == "__main__":
    unittest.main()
