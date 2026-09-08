"""A skill's identity comes from its frontmatter, not its filename."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common.skill_catalog import SkillCatalog


class SkillCatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)

    def _write(self, filename: str, text: str) -> None:
        (self.directory / filename).write_text(text, encoding="utf-8")

    def test_the_name_comes_from_frontmatter_not_the_filename(self) -> None:
        self._write("SKILL.md", "---\nname: aimel\ndescription: talk by email\n---\n\n# aimel\n")

        skill = SkillCatalog(self.directory).find("aimel")

        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "aimel")
        self.assertEqual(skill.summary, "talk by email")

    def test_a_skill_with_no_frontmatter_falls_back_to_filename_and_first_prose_line(self) -> None:
        self._write("notes.md", "# heading\n\nThe first real sentence.\n")

        skill = SkillCatalog(self.directory).find("notes")

        self.assertEqual(skill.name, "notes")
        self.assertEqual(skill.summary, "The first real sentence.")

    def test_the_frontmatter_delimiter_is_never_mistaken_for_the_summary(self) -> None:
        self._write("SKILL.md", "---\nname: x\n---\n\n# x\n\nReal prose.\n")

        self.assertEqual(SkillCatalog(self.directory).find("x").summary, "Real prose.")

    def test_byte_count_counts_utf8_bytes(self) -> None:
        self._write("SKILL.md", "---\nname: x\ndescription: d\n---\n\ncafé\n")

        skill = SkillCatalog(self.directory).find("x")

        self.assertEqual(skill.byte_count, len(skill.markdown.encode("utf-8")))
        self.assertGreater(skill.byte_count, len(skill.markdown))

    def test_an_unknown_name_is_none_and_a_missing_directory_is_empty(self) -> None:
        self.assertIsNone(SkillCatalog(self.directory).find("nope"))
        self.assertEqual(SkillCatalog(self.directory / "gone").all(), [])


if __name__ == "__main__":
    unittest.main()
