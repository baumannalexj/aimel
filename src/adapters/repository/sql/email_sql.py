"""Every statement the email repository runs, written out in full.

Values are always named binds — there is no interpolation of caller data anywhere in this module,
so there is nothing to sanitise. Where a table name genuinely varies it goes through
`IDatabaseClient.identifier()`, which validates it rather than trusting it.
"""

from __future__ import annotations

from domain.message import MessageState

# uuid is unique because it identifies one email; thread_uuid is not, because a thread has many.
_IDENTITY = """
    pk             INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid           TEXT NOT NULL UNIQUE DEFAULT (lower(
                       hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' ||
                       substr(hex(randomblob(2)), 2) || '-' ||
                       substr('89ab', abs(random()) % 4 + 1, 1) ||
                       substr(hex(randomblob(2)), 2) || '-' || hex(randomblob(6)))),
    thread_uuid    TEXT NOT NULL DEFAULT (lower(
                       hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' ||
                       substr(hex(randomblob(2)), 2) || '-' ||
                       substr('89ab', abs(random()) % 4 + 1, 1) ||
                       substr(hex(randomblob(2)), 2) || '-' || hex(randomblob(6)))),
    created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    session        TEXT NOT NULL,
    subject        TEXT NOT NULL,
    sender         TEXT NOT NULL,
    recipient      TEXT NOT NULL,
    author         TEXT NOT NULL,
    rfc_message_id TEXT NOT NULL,
    in_reply_to    TEXT NOT NULL DEFAULT '',
    refs           TEXT NOT NULL DEFAULT '',
    body_html      TEXT NOT NULL DEFAULT '',
    body_text      TEXT NOT NULL DEFAULT '',
    sent_at        TEXT NOT NULL"""

CREATE_TABLE = {
    MessageState.UNREAD: f"""
        CREATE TABLE IF NOT EXISTS unread ({_IDENTITY}
        )""",
    MessageState.READ: f"""
        CREATE TABLE IF NOT EXISTS read ({_IDENTITY},
            read_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        )""",
    MessageState.DELETED: f"""
        CREATE TABLE IF NOT EXISTS deleted ({_IDENTITY},
            previous_state TEXT NOT NULL,
            deleted_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        )""",
}

# --- writes ---

# thread_uuid is omitted, so the schema default mints a new one.
INSERT_NEW_THREAD = """
    INSERT INTO unread (
        session, subject, sender, recipient, author,
        rfc_message_id, in_reply_to, refs, body_html, body_text, sent_at
    ) VALUES (
        :session, :subject, :sender, :recipient, :author,
        :rfc_message_id, :in_reply_to, :refs, :body_html, :body_text, :sent_at
    )"""

# thread_uuid is looked up from the answered email and bound explicitly.
INSERT_REPLY = """
    INSERT INTO unread (
        thread_uuid,
        session, subject, sender, recipient, author,
        rfc_message_id, in_reply_to, refs, body_html, body_text, sent_at
    ) VALUES (
        :thread_uuid,
        :session, :subject, :sender, :recipient, :author,
        :rfc_message_id, :in_reply_to, :refs, :body_html, :body_text, :sent_at
    )"""

# A move keeps the original identity; only the state timestamp is schema-stamped.
INSERT_MOVED_READ = """
    INSERT INTO read (
        uuid, thread_uuid, created_at,
        session, subject, sender, recipient, author,
        rfc_message_id, in_reply_to, refs, body_html, body_text, sent_at
    ) VALUES (
        :uuid, :thread_uuid, :created_at,
        :session, :subject, :sender, :recipient, :author,
        :rfc_message_id, :in_reply_to, :refs, :body_html, :body_text, :sent_at
    )"""

INSERT_MOVED_DELETED = """
    INSERT INTO deleted (
        uuid, thread_uuid, created_at, previous_state,
        session, subject, sender, recipient, author,
        rfc_message_id, in_reply_to, refs, body_html, body_text, sent_at
    ) VALUES (
        :uuid, :thread_uuid, :created_at, :previous_state,
        :session, :subject, :sender, :recipient, :author,
        :rfc_message_id, :in_reply_to, :refs, :body_html, :body_text, :sent_at
    )"""

DELETE_BY_UUID = {
    MessageState.UNREAD: "DELETE FROM unread  WHERE uuid = :uuid",
    MessageState.READ: "DELETE FROM read    WHERE uuid = :uuid",
    MessageState.DELETED: "DELETE FROM deleted WHERE uuid = :uuid",
}

# --- reads ---

SELECT_BY_UUID = {
    MessageState.UNREAD: "SELECT * FROM unread  WHERE uuid = :uuid LIMIT 1",
    MessageState.READ: "SELECT * FROM read    WHERE uuid = :uuid LIMIT 1",
    MessageState.DELETED: "SELECT * FROM deleted WHERE uuid = :uuid LIMIT 1",
}

SELECT_BY_RFC = {
    MessageState.UNREAD: "SELECT * FROM unread  WHERE rfc_message_id = :rfc LIMIT 1",
    MessageState.READ: "SELECT * FROM read    WHERE rfc_message_id = :rfc LIMIT 1",
    MessageState.DELETED: "SELECT * FROM deleted WHERE rfc_message_id = :rfc LIMIT 1",
}

SELECT_BY_THREAD = {
    MessageState.UNREAD: "SELECT * FROM unread  WHERE thread_uuid = :thread_uuid",
    MessageState.READ: "SELECT * FROM read    WHERE thread_uuid = :thread_uuid",
    MessageState.DELETED: "SELECT * FROM deleted WHERE thread_uuid = :thread_uuid",
}

SELECT_ALL_IN_STATE = {
    MessageState.UNREAD: "SELECT * FROM unread  ORDER BY sent_at DESC LIMIT :limit",
    MessageState.READ: "SELECT * FROM read    ORDER BY sent_at DESC LIMIT :limit",
    MessageState.DELETED: "SELECT * FROM deleted ORDER BY sent_at DESC LIMIT :limit",
}

SELECT_LAST_INSERTED = """
    SELECT *
    FROM unread
    WHERE pk = last_insert_rowid()"""

SELECT_UNREAD_FOR_RECIPIENT = """
    SELECT *
    FROM unread
    WHERE recipient = :recipient
    ORDER BY sent_at DESC
    LIMIT :limit"""

SELECT_THREAD_UUID_BY_EMAIL = """
    SELECT thread_uuid
    FROM (
        SELECT uuid, thread_uuid FROM unread
        UNION ALL
        SELECT uuid, thread_uuid FROM read
        UNION ALL
        SELECT uuid, thread_uuid FROM deleted
    )
    WHERE uuid = :email_id
    LIMIT 1"""

SELECT_ALL_THREADS = """
    SELECT session,
           thread_uuid,
           subject,
           COUNT(*)     AS count,
           MAX(sent_at) AS updated_at
    FROM (
        SELECT session, thread_uuid, subject, sent_at FROM unread
        UNION ALL
        SELECT session, thread_uuid, subject, sent_at FROM read
        UNION ALL
        SELECT session, thread_uuid, subject, sent_at FROM deleted
    )
    GROUP BY thread_uuid
    ORDER BY updated_at DESC
    LIMIT :limit"""

SELECT_THREADS_FOR_SESSION = """
    SELECT thread_uuid,
           subject,
           COUNT(*)     AS count,
           MAX(sent_at) AS updated_at
    FROM (
        SELECT thread_uuid, subject, sent_at FROM unread  WHERE session = :session
        UNION ALL
        SELECT thread_uuid, subject, sent_at FROM read    WHERE session = :session
        UNION ALL
        SELECT thread_uuid, subject, sent_at FROM deleted WHERE session = :session
    )
    GROUP BY thread_uuid
    ORDER BY updated_at DESC"""

SELECT_LATEST_EMAIL_IN_THREAD = """
    SELECT uuid
    FROM (
        SELECT uuid, thread_uuid, sent_at FROM unread
        UNION ALL
        SELECT uuid, thread_uuid, sent_at FROM read
        UNION ALL
        SELECT uuid, thread_uuid, sent_at FROM deleted
    )
    WHERE thread_uuid = :thread_uuid
    ORDER BY sent_at DESC
    LIMIT 1"""
