"""Every statement the session repository runs, written out in full.

Values are always named binds — there is no interpolation of caller data anywhere in this module,
so there is nothing to sanitise. Where a table name genuinely varies it goes through
`IDatabaseClient.identifier()`, which validates it rather than trusting it.
"""

from __future__ import annotations

# `uuid` is the row's own opaque identity, minted the same way email/thread uuids are.
# `session_id` is the natural key: the Claude session uuid the agent already mints itself.
CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS sessions (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid         TEXT NOT NULL UNIQUE DEFAULT (lower(
                         hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' ||
                         substr(hex(randomblob(2)), 2) || '-' ||
                         substr('89ab', abs(random()) % 4 + 1, 1) ||
                         substr(hex(randomblob(2)), 2) || '-' || hex(randomblob(6)))),
        created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
        session_id   TEXT NOT NULL UNIQUE,
        last_seen_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
        email_count  INTEGER NOT NULL DEFAULT 0
    )"""

# --- writes ---

# An UPSERT: the first email inserts the row with email_count = 1; every later one lands on the
# unique session_id instead of violating it, and bumps last_seen_at/email_count in the same
# statement. One round trip, no separate "does it exist" check, so nothing can race between the two.
REGISTER = """
    INSERT INTO sessions (session_id, email_count)
    VALUES (:session_id, 1)
    ON CONFLICT (session_id) DO UPDATE SET
        last_seen_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now'),
        email_count  = email_count + 1"""

# --- reads ---

SELECT_BY_SESSION_ID = """
    SELECT * FROM sessions WHERE session_id = :session_id LIMIT 1"""

SELECT_ALL = """
    SELECT * FROM sessions ORDER BY last_seen_at DESC"""
