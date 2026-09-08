from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from application.main import CliApplication
from common.config import ConfigLoader


class SettingsCommandTest(unittest.TestCase):
    """`settings --set` takes a dotted path into the config shape and validates before saving."""

    def setUp(self) -> None:
        self._settings_path = Path(tempfile.mkdtemp()) / "settings.json"

    def _run(self, *argv: str) -> str:
        app = CliApplication(ConfigLoader(settings_path=self._settings_path, environ={}))
        out = io.StringIO()
        with redirect_stdout(out):
            app.run(["settings", *argv])
        return out.getvalue()

    def test_a_dotted_key_sets_a_nested_field(self) -> None:
        self._run("--set", "smtpConfig.port=2025")

        saved = json.loads(self._settings_path.read_text())
        self.assertEqual(saved["smtpConfig"]["port"], "2025")

    def test_an_invalid_setting_is_rejected_before_saving(self) -> None:
        with self.assertRaises(SystemExit):
            self._run("--set", "smtpConfig.port=not-a-number")

        self.assertFalse(self._settings_path.exists())


class ServeDefaultsTest(unittest.TestCase):
    def test_serve_takes_its_port_from_config_not_argparse(self) -> None:
        """argparse cannot know the flag, so an unspecified port stays unresolved here."""
        args = CliApplication.parser().parse_args(["serve"])

        self.assertIsNone(args.port)
        self.assertEqual(args.host, "127.0.0.1")

    def test_an_explicit_port_still_wins(self) -> None:
        self.assertEqual(CliApplication.parser().parse_args(["serve", "--port", "9000"]).port, 9000)


if __name__ == "__main__":
    unittest.main()
