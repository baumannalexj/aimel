"""Reports what someone would actually want to know about the mail store's size.

Row counts, content bytes, and the freelist are SQL facts and go through IDatabaseClient like
every other read in this codebase. File sizes are not a SQL fact -- the WAL and SHM sidecars
aren't visible through the client at all, since it hides the connection rather than the path --
so they're read straight off disk via the same path the config hands out everywhere else
(`config.database.path`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from domain.message import MessageState
from ports.database_client import IDatabaseClient


@dataclass(frozen=True)
class DatabaseFileSizes:
    """On-disk bytes for the database file and its WAL/SHM sidecars. The WAL can outgrow the db."""

    database_bytes: int
    wal_bytes: int
    shm_bytes: int

    @property
    def total_bytes(self) -> int:
        return self.database_bytes + self.wal_bytes + self.shm_bytes


@dataclass(frozen=True)
class TableRowCounts:
    """Row counts per state table."""

    unread: int
    read: int
    deleted: int

    @property
    def total(self) -> int:
        return self.unread + self.read + self.deleted


@dataclass(frozen=True)
class ContentSizeReport:
    """How much of the database file is message content versus SQLite page overhead."""

    content_bytes: int
    database_bytes: int

    @property
    def overhead_bytes(self) -> int:
        return self.database_bytes - self.content_bytes


@dataclass(frozen=True)
class ReclaimableSpace:
    """Free pages SQLite is holding onto after deletes. Reported, not offered as a VACUUM."""

    freelist_pages: int
    page_size: int

    @property
    def reclaimable_bytes(self) -> int:
        return self.freelist_pages * self.page_size


@dataclass(frozen=True)
class DatabaseStatsReport:
    file_sizes: DatabaseFileSizes
    row_counts: TableRowCounts
    content: ContentSizeReport
    reclaimable: ReclaimableSpace


class DatabaseStats:
    """Collects the size indicator: file sizes straight off disk, everything else via SQL."""

    def __init__(self, database_client: IDatabaseClient, database_path: Path):
        self._db = database_client
        self._path = database_path

    def collect(self) -> DatabaseStatsReport:
        file_sizes = self._file_sizes()
        return DatabaseStatsReport(
            file_sizes=file_sizes,
            row_counts=self._row_counts(),
            content=self._content_size(file_sizes.database_bytes),
            reclaimable=self._reclaimable_space(),
        )

    def _file_sizes(self) -> DatabaseFileSizes:
        return DatabaseFileSizes(
            database_bytes=_file_size(self._path),
            wal_bytes=_file_size(self._path.with_name(self._path.name + "-wal")),
            shm_bytes=_file_size(self._path.with_name(self._path.name + "-shm")),
        )

    def _row_counts(self) -> TableRowCounts:
        return TableRowCounts(
            unread=self._count(MessageState.UNREAD),
            read=self._count(MessageState.READ),
            deleted=self._count(MessageState.DELETED),
        )

    def _count(self, state: MessageState) -> int:
        table = self._db.identifier(state.value)
        rows = self._db.query(f"SELECT COUNT(*) AS count FROM {table}")
        return rows[0]["count"]

    def _content_size(self, database_bytes: int) -> ContentSizeReport:
        content_bytes = sum(self._content_bytes(state) for state in MessageState)
        return ContentSizeReport(content_bytes=content_bytes, database_bytes=database_bytes)

    def _content_bytes(self, state: MessageState) -> int:
        table = self._db.identifier(state.value)
        rows = self._db.query(
            f"SELECT COALESCE(SUM(length(body_html) + length(body_text)), 0) AS bytes "
            f"FROM {table}"
        )
        return rows[0]["bytes"]

    def _reclaimable_space(self) -> ReclaimableSpace:
        freelist = self._db.query("PRAGMA freelist_count")[0]["freelist_count"]
        page_size = self._db.query("PRAGMA page_size")[0]["page_size"]
        return ReclaimableSpace(freelist_pages=freelist, page_size=page_size)


def _file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0
