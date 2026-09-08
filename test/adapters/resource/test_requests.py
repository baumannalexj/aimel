from __future__ import annotations

import unittest

from pydantic import ValidationError

from adapters.resource.requests import ReplyRequest, SendNewThreadRequest

SESSION = "0bd9c0c5-5b21-44be-9a3b-2793b5788d05"
EMAIL_ID = "11111111-2222-4333-8444-555555555555"


class SendNewThreadRequestBodyTest(unittest.TestCase):
    def test_rejects_an_email_with_no_body(self) -> None:
        with self.assertRaises(ValidationError):
            SendNewThreadRequest(session=SESSION, title="hello", html="")

    def test_accepts_an_email_with_a_body(self) -> None:
        request = SendNewThreadRequest(session=SESSION, title="hello", html="<p>hi</p>")
        self.assertEqual(request.html, "<p>hi</p>")

    def test_no_longer_accepts_a_text_field(self) -> None:
        with self.assertRaises(ValidationError):
            SendNewThreadRequest(session=SESSION, title="hello", html="<p>hi</p>", text="hi")


class ReplyRequestBodyTest(unittest.TestCase):
    def test_rejects_a_reply_with_no_body(self) -> None:
        with self.assertRaises(ValidationError):
            ReplyRequest(session=SESSION, email_id=EMAIL_ID, html="")

    def test_accepts_a_reply_with_a_body(self) -> None:
        request = ReplyRequest(session=SESSION, email_id=EMAIL_ID, html="<p>hi</p>")
        self.assertEqual(request.html, "<p>hi</p>")

    def test_no_longer_accepts_a_text_field(self) -> None:
        with self.assertRaises(ValidationError):
            ReplyRequest(session=SESSION, email_id=EMAIL_ID, html="<p>hi</p>", text="hi")


if __name__ == "__main__":
    unittest.main()
