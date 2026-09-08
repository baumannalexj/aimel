from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from common.session_directory import SessionDirectory

SESSION_A = "aaaaaaaa-0000-4000-8000-000000000001"
SESSION_B = "bbbbbbbb-0000-4000-8000-000000000002"
SESSION_C = "cccccccc-0000-4000-8000-000000000003"


def _line(**fields: object) -> str:
    return json.dumps(fields) + "\n"


def _user_line(text: str) -> str:
    return _line(type="user", message={"role": "user", "content": text})


class SessionDirectoryTest(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self._root = Path(directory.name)

    def _write(self, project: str, session_uuid: str, lines: list[str], age_seconds: float = 0) -> None:
        project_dir = self._root / project
        project_dir.mkdir(parents=True, exist_ok=True)
        path = project_dir / f"{session_uuid}.jsonl"
        path.write_text("".join(lines))
        if age_seconds:
            stamp = time.time() - age_seconds
            os.utime(path, (stamp, stamp))

    def test_reads_the_project_and_first_user_message(self) -> None:
        self._write(
            "-Users-alexander-baumann-toast",
            SESSION_A,
            [
                _line(type="summary", leafUuid="x"),
                _user_line("first thing I asked"),
                _user_line("a later message that must not win"),
            ],
        )

        [session] = SessionDirectory(self._root).list_sessions()

        self.assertEqual(session.session_uuid, SESSION_A)
        self.assertEqual(session.project, "/Users/alexander/baumann/toast")
        self.assertEqual(session.context, "first thing I asked")

    def test_most_recently_active_session_comes_first(self) -> None:
        self._write("-a", SESSION_A, [_user_line("older")], age_seconds=120)
        self._write("-b", SESSION_B, [_user_line("newer")], age_seconds=10)

        sessions = SessionDirectory(self._root).list_sessions()

        self.assertEqual([s.session_uuid for s in sessions], [SESSION_B, SESSION_A])

    def test_a_malformed_line_is_skipped_rather_than_failing_the_listing(self) -> None:
        self._write(
            "-a",
            SESSION_A,
            ["not json at all\n", "{\n", _user_line("the real first message")],
        )

        [session] = SessionDirectory(self._root).list_sessions()

        self.assertEqual(session.context, "the real first message")

    def test_a_file_with_no_user_message_gets_an_empty_context_not_an_error(self) -> None:
        self._write(
            "-a",
            SESSION_A,
            [_line(type="summary", leafUuid="x"), _line(type="assistant", message={"role": "assistant"})],
        )

        [session] = SessionDirectory(self._root).list_sessions()

        self.assertEqual(session.context, "")

    def test_user_lines_with_non_string_content_are_not_the_context(self) -> None:
        """A tool-result turn is still `type: user`, but its content is a block list, not text."""
        self._write(
            "-a",
            SESSION_A,
            [
                _line(type="user", message={"role": "user", "content": [{"type": "tool_result"}]}),
                _user_line("the actual first prompt"),
            ],
        )

        [session] = SessionDirectory(self._root).list_sessions()

        self.assertEqual(session.context, "the actual first prompt")

    def test_subagent_transcripts_are_skipped_without_being_opened(self) -> None:
        project_dir = self._root / "-a"
        subagents = project_dir / SESSION_A / "subagents"
        subagents.mkdir(parents=True)
        (subagents / "agent-a1b2c3d4e5f6.jsonl").write_text("this would blow up if it were read\n")
        self._write("-a", SESSION_A, [_user_line("the one real session")])

        sessions = SessionDirectory(self._root).list_sessions()

        self.assertEqual([s.session_uuid for s in sessions], [SESSION_A])

    def test_limit_caps_the_result(self) -> None:
        self._write("-a", SESSION_A, [_user_line("a")], age_seconds=30)
        self._write("-b", SESSION_B, [_user_line("b")], age_seconds=20)
        self._write("-c", SESSION_C, [_user_line("c")], age_seconds=10)

        sessions = SessionDirectory(self._root).list_sessions(limit=2)

        self.assertEqual([s.session_uuid for s in sessions], [SESSION_C, SESSION_B])

    def test_a_missing_projects_root_is_an_empty_list_not_an_error(self) -> None:
        sessions = SessionDirectory(self._root / "does-not-exist").list_sessions()

        self.assertEqual(sessions, [])


if __name__ == "__main__":
    unittest.main()


class SessionDirectoryProjectPathTest(unittest.TestCase):
    """The directory name cannot round-trip a path containing a dot, so the transcript wins."""

    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def _write(self, slug: str, uuid: str, lines: list[dict]) -> None:
        folder = self.root / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{uuid}.jsonl").write_text("\n".join(json.dumps(line) for line in lines))

    def test_a_dotted_path_comes_from_the_transcript_not_the_directory_name(self) -> None:
        self._write(
            "-Users-alexander-baumann-toast",
            "11111111-2222-4333-8444-555555555555",
            [
                {"type": "summary"},
                {"type": "user", "cwd": "/Users/alexander.baumann/toast",
                 "message": {"content": "first thing I said"}},
            ],
        )

        session = SessionDirectory(self.root).list_sessions()[0]

        self.assertEqual(session.project, "/Users/alexander.baumann/toast")
        self.assertEqual(session.context, "first thing I said")

    def test_falls_back_to_the_directory_name_when_no_line_states_a_cwd(self) -> None:
        self._write(
            "-Users-someone-repo",
            "22222222-3333-4444-8555-666677778888",
            [{"type": "user", "message": {"content": "no cwd anywhere"}}],
        )

        session = SessionDirectory(self.root).list_sessions()[0]

        self.assertEqual(session.project, "/Users/someone/repo")
