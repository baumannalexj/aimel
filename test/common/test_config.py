from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlparse

from common import repo_paths
from common.config import ConfigLoader, DefaultPortOwner

NOWHERE = Path("/nonexistent/settings.json")


def load(**environ: str):
    return ConfigLoader(settings_path=NOWHERE, environ=environ).load()


class DefaultPortOwnerTest(unittest.TestCase):
    """A flag decides which app owns 8025, so the familiar dashboard stays reachable there."""

    def test_the_spool_owns_the_default_port_unless_told_otherwise(self) -> None:
        config = load()

        self.assertIs(config.web.default_port_owner, DefaultPortOwner.SPOOL)
        self.assertEqual(config.web.spool_port, 8025)
        self.assertEqual(config.web.reply_port, 8026)

    def test_flipping_the_flag_hands_the_default_port_to_the_reply_client(self) -> None:
        config = load(AIMEL_WEB_DEFAULT_PORT_OWNER="reply")

        self.assertIs(config.web.default_port_owner, DefaultPortOwner.REPLY)
        self.assertEqual(config.web.reply_port, 8025)
        self.assertEqual(config.web.spool_port, 8027)

    def test_api_base_follows_the_spool_rather_than_being_set_twice(self) -> None:
        self.assertEqual(urlparse(load().mailbox.api_base).port, 8025)
        self.assertEqual(
            urlparse(load(AIMEL_WEB_DEFAULT_PORT_OWNER="reply").mailbox.api_base).port, 8027
        )

    def test_the_two_apps_never_share_a_port(self) -> None:
        for environ in ({}, {"AIMEL_WEB_DEFAULT_PORT_OWNER": "reply"}):
            config = ConfigLoader(settings_path=NOWHERE, environ=environ).load()
            self.assertNotEqual(
                config.web.spool_port, config.web.reply_port, f"collision with {environ}"
            )

    def test_compose_takes_the_spool_port_from_config(self) -> None:
        """Catches compose and config drifting apart, which is invisible until a request fails."""
        compose = repo_paths.compose_file().read_text()
        self.assertIsNotNone(
            re.search(r"\$\{AIMEL_HTTP_PORT[^}]*\}", compose),
            "compose no longer takes the http port from the environment",
        )


class ConfigLayeringTest(unittest.TestCase):
    """config.json is the committed baseline; config.local.json and env overrides layer on top."""

    def setUp(self) -> None:
        self._repo_root = Path(tempfile.mkdtemp())
        (self._repo_root / "config.json").write_text(json.dumps({
            "mailDir": "~/_claude-email",
            "purgeAfterDrain": False,
            "smtpConfig": {"host": "localhost", "port": 1025},
            "databaseConfig": {"timeoutSeconds": 5.0},
            "namingConfig": {
                "serviceName": "aimel", "domain": "aimel.com",
                "humanAddress": "{user}@{domain}", "agentAddress": "claude-{session8}@{domain}",
                "subjectTemplate": "{title}",
            },
            "webConfig": {
                "defaultPortOwner": "spool", "defaultPort": 8025,
                "spoolAlternatePort": 8027, "replyAlternatePort": 8026,
            },
            "skillConfig": {"targetDir": "~/.claude/skills/aimel"},
        }))

    def _load(self, **environ: str):
        environ = {"AIMEL_REPO_ROOT": str(self._repo_root), **environ}
        return ConfigLoader(settings_path=NOWHERE, environ=environ).load()

    def test_config_local_json_overrides_a_single_nested_field(self) -> None:
        """The rest of smtpConfig keeps its default, since the merge is per-field, not per-file."""
        (self._repo_root / "config.local.json").write_text(
            json.dumps({"smtpConfig": {"port": 2025}})
        )

        config = self._load()

        self.assertEqual(config.smtp.port, 2025)
        self.assertEqual(config.smtp.host, "localhost")

    def test_an_explicit_env_var_wins_over_config_local_json(self) -> None:
        (self._repo_root / "config.local.json").write_text(
            json.dumps({"smtpConfig": {"port": 2025}})
        )

        config = self._load(AIMEL_SMTP_PORT="3025")

        self.assertEqual(config.smtp.port, 3025)

    def test_missing_config_local_json_is_fine(self) -> None:
        self.assertEqual(self._load().smtp.host, "localhost")


if __name__ == "__main__":
    unittest.main()
