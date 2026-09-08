"""Every statement the email repository runs, written out in full.

Values are always named binds — there is no interpolation of caller data anywhere in this module,
so there is nothing to sanitise. Where a table name genuinely varies it goes through
`IDatabaseClient.identifier()`, which validates it rather than trusting it.

Storage is relational: a thread's subject lives once on `threads`, an email's content lives once on
`emails`, and `unread`/`read`/`deleted` hold nothing but a reference to `emails.id`. State is which of
those three tables has a row for a given email, not a copy of its columns.
"""

from __future__ import annotations

from domain.message import MessageState

_UUID_DEFAULT = """DEFAULT (lower(
        hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' ||
        substr(hex(randomblob(2)), 2) || '-' ||
        substr('89ab', abs(random()) % 4 + 1, 1) ||
        substr(hex(randomblob(2)), 2) || '-' || hex(randomblob(6))))"""

_CREATED_AT_DEFAULT = "DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))"

CREATE_THREADS_TABLE = f"""
    CREATE TABLE IF NOT EXISTS threads (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid       TEXT NOT NULL UNIQUE {_UUID_DEFAULT},
        subject    TEXT NOT NULL,
        created_at TEXT NOT NULL {_CREATED_AT_DEFAULT}
    )"""

CREATE_EMAILS_TABLE = f"""
    CREATE TABLE IF NOT EXISTS emails (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid           TEXT NOT NULL UNIQUE {_UUID_DEFAULT},
        thread_id      INTEGER NOT NULL REFERENCES threads (id),
        session        TEXT NOT NULL,
        sender         TEXT NOT NULL,
        recipient      TEXT NOT NULL,
        author         TEXT NOT NULL,
        rfc_message_id TEXT NOT NULL,
        in_reply_to    TEXT NOT NULL DEFAULT '',
        refs           TEXT NOT NULL DEFAULT '',
        body_html      TEXT NOT NULL DEFAULT '',
        body_text      TEXT NOT NULL DEFAULT '',
        sent_at        TEXT NOT NULL,
        created_at     TEXT NOT NULL {_CREATED_AT_DEFAULT}
    )"""

CREATE_UNREAD_TABLE = """
    CREATE TABLE IF NOT EXISTS unread (
        email_id INTEGER PRIMARY KEY REFERENCES emails (id)
    )"""

CREATE_READ_TABLE = f"""
    CREATE TABLE IF NOT EXISTS read (
        email_id INTEGER PRIMARY KEY REFERENCES emails (id),
        read_at  TEXT NOT NULL {_CREATED_AT_DEFAULT}
    )"""

CREATE_DELETED_TABLE = f"""
    CREATE TABLE IF NOT EXISTS deleted (
        email_id       INTEGER PRIMARY KEY REFERENCES emails (id),
        deleted_at     TEXT NOT NULL {_CREATED_AT_DEFAULT},
        previous_state TEXT NOT NULL
    )"""

CREATE_INDEX_EMAILS_SESSION = """
    CREATE INDEX IF NOT EXISTS emails_session_sent_at ON emails (session, sent_at)"""

CREATE_INDEX_EMAILS_THREAD = """
    CREATE INDEX IF NOT EXISTS emails_thread_id_sent_at ON emails (thread_id, sent_at)"""

# --- writes ---

INSERT_THREAD = "INSERT INTO threads (subject) VALUES (:subject)"

# thread_id is the threads row just inserted above, in the same transaction.
INSERT_EMAIL_FOR_NEW_THREAD = """
    INSERT INTO emails (
        thread_id,
        session, sender, recipient, author,
        rfc_message_id, in_reply_to, refs, body_html, body_text, sent_at
    ) VALUES (
        last_insert_rowid(),
        :session, :sender, :recipient, :author,
        :rfc_message_id, :in_reply_to, :refs, :body_html, :body_text, :sent_at
    )"""

# thread_id is looked up from the answered email and bound explicitly.
INSERT_EMAIL_FOR_REPLY = """
    INSERT INTO emails (
        thread_id,
        session, sender, recipient, author,
        rfc_message_id, in_reply_to, refs, body_html, body_text, sent_at
    ) VALUES (
        :thread_id,
        :session, :sender, :recipient, :author,
        :rfc_message_id, :in_reply_to, :refs, :body_html, :body_text, :sent_at
    )"""

# email_id is the emails row just inserted above, in the same transaction.
INSERT_UNREAD = "INSERT INTO unread (email_id) VALUES (last_insert_rowid())"

INSERT_READ = """
    INSERT INTO read (email_id)
    VALUES ((SELECT id FROM emails WHERE uuid = :uuid))"""

INSERT_DELETED = """
    INSERT INTO deleted (email_id, previous_state)
    VALUES ((SELECT id FROM emails WHERE uuid = :uuid), :previous_state)"""

DELETE_BY_UUID = {
    MessageState.UNREAD: "DELETE FROM unread  WHERE email_id = (SELECT id FROM emails WHERE uuid = :uuid)",
    MessageState.READ: "DELETE FROM read    WHERE email_id = (SELECT id FROM emails WHERE uuid = :uuid)",
    MessageState.DELETED: "DELETE FROM deleted WHERE email_id = (SELECT id FROM emails WHERE uuid = :uuid)",
}

# --- reads ---

# One indexed pass, no union: state falls out of which of read/deleted has a matching row.
_EMAIL_JOIN = """
    SELECT e.uuid, e.session, e.sender, e.recipient, e.author,
           e.rfc_message_id, e.in_reply_to, e.refs, e.body_html, e.body_text,
           e.sent_at, e.created_at,
           t.uuid AS thread_uuid, t.subject AS subject,
           r.read_at AS read_at,
           d.deleted_at AS deleted_at, d.previous_state AS previous_state,
           CASE WHEN d.email_id IS NOT NULL THEN 'deleted'
                WHEN r.email_id IS NOT NULL THEN 'read'
                ELSE 'unread' END AS state
    FROM emails e
    JOIN threads t      ON t.id = e.thread_id
    LEFT JOIN read    r ON r.email_id = e.id
    LEFT JOIN deleted d ON d.email_id = e.id"""

SELECT_BY_UUID = f"""{_EMAIL_JOIN}
    WHERE e.uuid = :uuid
    LIMIT 1"""

SELECT_BY_RFC = f"""{_EMAIL_JOIN}
    WHERE e.rfc_message_id = :rfc
    LIMIT 1"""

SELECT_BY_THREAD = f"""{_EMAIL_JOIN}
    WHERE e.thread_id = :thread_id
    ORDER BY e.sent_at DESC"""

SELECT_ALL_IN_STATE = {
    MessageState.UNREAD: f"""{_EMAIL_JOIN}
        WHERE r.email_id IS NULL AND d.email_id IS NULL
        ORDER BY e.sent_at DESC
        LIMIT :limit""",
    MessageState.READ: f"""{_EMAIL_JOIN}
        WHERE r.email_id IS NOT NULL AND d.email_id IS NULL
        ORDER BY e.sent_at DESC
        LIMIT :limit""",
    MessageState.DELETED: f"""{_EMAIL_JOIN}
        WHERE d.email_id IS NOT NULL
        ORDER BY e.sent_at DESC
        LIMIT :limit""",
}

SELECT_LAST_INSERTED = f"""{_EMAIL_JOIN}
    WHERE e.id = last_insert_rowid()"""

SELECT_UNREAD_FOR_RECIPIENT = f"""{_EMAIL_JOIN}
    WHERE e.recipient = :recipient
      AND r.email_id IS NULL AND d.email_id IS NULL
    ORDER BY e.sent_at DESC
    LIMIT :limit"""

SELECT_THREAD_ID_BY_EMAIL_UUID = """
    SELECT thread_id
    FROM emails
    WHERE uuid = :uuid
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
    SELECT t.id         AS thread_id,
           t.uuid        AS thread_uuid,
           t.subject     AS subject,
           COUNT(*)      AS count,
           MAX(e.sent_at) AS updated_at
    FROM emails e
    JOIN threads t ON t.id = e.thread_id
    WHERE e.session = :session
    GROUP BY t.id
    ORDER BY updated_at DESC"""

SELECT_LATEST_EMAIL_IN_THREAD = """
    SELECT uuid
    FROM emails
    WHERE thread_id = :thread_id
    ORDER BY sent_at DESC
    LIMIT 1"""
