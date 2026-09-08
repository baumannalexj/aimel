from __future__ import annotations

import re
import smtplib
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid

from common.config import SmtpConfig
from domain.message import HtmlBody, now
from domain.outgoing import Envelope
from ports.email_transport import IEmailTransport


class SmtpEmailTransport(IEmailTransport):
    def __init__(self, config: SmtpConfig):
        self._config = config

    def send(self, envelope: Envelope, body_html: HtmlBody, body_text: str) -> str:
        prefix = f"X-{self._config.service_name.title()}"
        message = EmailMessage()
        message["From"] = str(envelope.sender)
        message["To"] = str(envelope.recipient)
        message["Subject"] = envelope.subject.text
        message["Date"] = format_datetime(now())
        rfc_message_id = make_msgid(domain=str(envelope.sender).split("@")[-1])
        message["Message-ID"] = rfc_message_id
        if envelope.in_reply_to:
            message["In-Reply-To"] = envelope.in_reply_to
        if envelope.references:
            message["References"] = " ".join(envelope.references)
        message[f"{prefix}-Session"] = str(envelope.session)
        message[f"{prefix}-Actor"] = envelope.actor.value
        message["X-Tags"] = str(envelope.session)
        message.set_content(body_text or body_html.to_plain_text())
        if body_html:
            message.add_alternative(body_html.markup, subtype="html")
        with smtplib.SMTP(self._config.host, self._config.port, timeout=10) as smtp:
            smtp.send_message(message)
        return rfc_message_id

