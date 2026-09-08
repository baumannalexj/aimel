from __future__ import annotations

import re
import unittest
from pathlib import Path
from urllib.parse import urlparse

from common.config import ConfigLoader

MAILPIT_HTTP_DEFAULT = 8027
REPLY_CLIENT_DEFAULT = 8025


class ConfigPortsTest(unittest.TestCase):
    """The reply client owns the default port; the spool's viewer moved off it."""

    def setUp(self) -> None:
        # No settings file, so these are the shipped defaults rather than the user's saved ones.
        self.config = ConfigLoader(settings_path=Path("/nonexistent/settings.json"), environ={}).load()

    def test_spool_api_is_not_on_the_default_port(self) -> None:
        self.assertEqual(urlparse(self.config.mailbox.api_base).port, MAILPIT_HTTP_DEFAULT)

    def test_compose_publishes_the_spool_on_the_same_port_config_expects(self) -> None:
        """Catches config and compose drifting apart, which is invisible until a request fails."""
        compose = self.config.paths.compose_file.read_text()
        published = re.search(r"\$\{AIMEL_HTTP_PORT:-(\d+)\}", compose)
        self.assertIsNotNone(published, "compose file no longer parameterises the http port")
        self.assertEqual(
            int(published.group(1)),
            urlparse(self.config.mailbox.api_base).port,
            "compose publishes the spool viewer on a different port than api_base points at",
        )

    def test_the_two_servers_cannot_collide(self) -> None:
        self.assertNotEqual(REPLY_CLIENT_DEFAULT, MAILPIT_HTTP_DEFAULT)


if __name__ == "__main__":
    unittest.main()
