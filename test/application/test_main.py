from __future__ import annotations

import unittest

from application.main import CliApplication


class ServeDefaultsTest(unittest.TestCase):
    def test_serve_listens_on_the_default_http_port(self) -> None:
        """The reply client is the thing you open, so it gets 8025."""
        args = CliApplication.parser().parse_args(["serve"])

        self.assertEqual(args.port, 8025)
        self.assertEqual(args.host, "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
