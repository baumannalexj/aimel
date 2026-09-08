from __future__ import annotations

import unittest
from datetime import datetime, timezone

from common.datetime_utils import from_iso8601_string, parse_or_now, to_iso8601_string


class DatetimeUtilsTest(unittest.TestCase):
    def test_round_trips_without_losing_precision_or_timezone(self) -> None:
        moment = datetime(2026, 9, 7, 22, 15, 30, 123456, tzinfo=timezone.utc)

        self.assertEqual(from_iso8601_string(to_iso8601_string(moment)), moment)

    def test_reads_the_z_suffix_the_schema_defaults_write(self) -> None:
        # SQLite's strftime default produces this shape, not an explicit offset.
        parsed = from_iso8601_string("2026-09-07T22:15:30Z")

        self.assertEqual(parsed, datetime(2026, 9, 7, 22, 15, 30, tzinfo=timezone.utc))
        self.assertIsNotNone(parsed.tzinfo)

    def test_assumes_utc_for_a_naive_value_so_comparisons_do_not_explode(self) -> None:
        parsed = from_iso8601_string("2026-09-07 22:15:30")

        self.assertEqual(parsed.tzinfo, timezone.utc)
        # The point of attaching it: this comparison would raise if the value stayed naive.
        self.assertLess(parsed, datetime.now(timezone.utc))

    def test_empty_blows_up_and_names_the_field(self) -> None:
        with self.assertRaises(ValueError) as caught:
            from_iso8601_string("", "deleted_at")

        self.assertIn("deleted_at", str(caught.exception))

    def test_intake_falls_back_to_now_when_upstream_sends_junk(self) -> None:
        self.assertAlmostEqual(
            parse_or_now("not a date").timestamp(),
            datetime.now(timezone.utc).timestamp(),
            delta=5,
        )


if __name__ == "__main__":
    unittest.main()
