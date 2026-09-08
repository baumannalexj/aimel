"""Domain errors, so callers branch on type rather than on message text.

An http status decided by substring-matching a message is one reword away from being wrong.
"""

from __future__ import annotations


class EmailNotFound(LookupError):
    def __init__(self, email_id: str):
        super().__init__(f"no such email: {email_id}")
        self.email_id = email_id


class EmailAlreadyDeleted(ValueError):
    def __init__(self, email_id: str):
        super().__init__(f"email is deleted: {email_id}")
        self.email_id = email_id
