from __future__ import annotations

import unittest

from application.main import CliApplication


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
