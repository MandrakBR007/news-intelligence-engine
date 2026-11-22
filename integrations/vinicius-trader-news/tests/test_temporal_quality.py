"""Temporal source-quality regression contracts using synthetic offline inputs."""
from datetime import datetime, timezone
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from news_engine import pipeline, store
from news_engine.feed_parsers import FeedItem, parse_json_list, parse_rss
from news_engine.util import parse_dt, parse_dt_details


class TemporalQualityTests(unittest.TestCase):
    def test_backward_compatible_parse_dt_return_type(self):
        self.assertEqual(parse_dt("2026-01-01T09:00:00"),
                         "2026-01-01T09:00:00+00:00")
        self.assertIsNone(parse_dt(None))
        self.assertEqual(parse_dt(datetime(2026, 1, 1, 9, tzinfo=timezone.utc)),
                         "2026-01-01T09:00:00+00:00")

    def test_quality_distinguishes_naive_and_explicit_timezone(self):
        for raw, expected_utc, quality in (
            ("2026-01-01T09:00:00", "2026-01-01T09:00:00+00:00",
             "reported_naive_utc"),
            ("2026-01-01T09:00:00-03:00", "2026-01-01T12:00:00+00:00",
             "reported_tz"),
            ("Thu, 01 Jan 2026 09:00:00 GMT", "2026-01-01T09:00:00+00:00",
             "reported_tz"),
            ("bad", None, "missing_or_invalid"),
            (None, None, "missing_or_invalid"),
        ):
            with self.subTest(raw=raw):
                self.assertEqual(parse_dt_details(raw), (expected_utc, quality))

    def test_future_timestamp_flagged_not_overwritten(self):
        observed = "2026-01-01T09:00:00+00:00"
        self.assertEqual(
            parse_dt_details("2026-01-03T09:00:01+00:00", observed_at=observed),
            ("2026-01-03T09:00:01+00:00", "future_suspect"),
        )
        self.assertEqual(
            parse_dt_details("2026-01-02T09:00:00+00:00", observed_at=observed)[1],
            "reported_tz",
        )
        # Invalid observation evidence must not fabricate a future flag.
        self.assertEqual(
            parse_dt_details("2026-01-03T09:00:01+00:00", observed_at="unknown")[1],
            "reported_tz",
        )

    def test_feed_parsers_preserve_source_timezone_quality(self):
        rss = (b"<rss><channel><item><title>Naive RSS date</title>"
               b"<pubDate>2026-01-01T09:00:00</pubDate></item>"
               b"</channel></rss>")
        parsed = parse_rss(rss, "fixture")[0]
        self.assertEqual(parsed.published_at, "2026-01-01T09:00:00+00:00")
        self.assertEqual(parsed.published_quality, "reported_naive_utc")
        json_data = (b'{"items":[{"title":"Explicit JSON offset",'
                     b'"published_at":"2026-01-01T09:00:00-03:00"}]}')
        item = parse_json_list(json_data, "fixture")[0]
        self.assertEqual(item.published_at, "2026-01-01T12:00:00+00:00")
        self.assertEqual(item.published_quality, "reported_tz")

    def test_pipeline_preserves_quality_from_parsed_item(self):
        with tempfile.TemporaryDirectory() as directory:
            conn = store.connect(Path(directory) / "news.db")
            try:
                store.init_db(conn)
                item = FeedItem(
                    "fixture", "id", "Sample title", "", "",
                    "2026-01-01T09:00:00+00:00", "reported_naive_utc")
                with mock.patch.object(
                    pipeline, "iso_now",
                    return_value="2026-01-01T11:00:00+00:00",
                ):
                    pipeline.process_items(conn, {"topics": [], "dedup": {}}, [item])
                row = dict(conn.execute("SELECT * FROM items").fetchone())
                self.assertEqual(row["published_quality"], "reported_naive_utc")
                self.assertEqual(row["first_seen_at"], row["ingested_at"])
                self.assertLessEqual(row["ingested_at"], row["classified_at"])
            finally:
                conn.close()

    def test_future_flag_takes_precedence_over_parser_quality(self):
        with tempfile.TemporaryDirectory() as directory:
            conn = store.connect(Path(directory) / "news.db")
            try:
                store.init_db(conn)
                item = FeedItem(
                    "fixture", "id", "Future headline", "", "",
                    "2026-02-01T00:00:00+00:00", "reported_naive_utc")
                with mock.patch.object(
                    pipeline, "iso_now",
                    return_value="2026-01-01T00:00:00+00:00",
                ):
                    pipeline.process_items(conn, {"topics": [], "dedup": {}}, [item])
                row = conn.execute("SELECT published_quality,published_at FROM items").fetchone()
                self.assertEqual(row["published_quality"], "future_suspect")
                self.assertEqual(row["published_at"], "2026-02-01T00:00:00+00:00")
            finally:
                conn.close()

    def test_legacy_rows_are_not_rewritten(self):
        with tempfile.TemporaryDirectory() as directory:
            conn = store.connect(Path(directory) / "news.db")
            try:
                store.init_db(conn)
                conn.execute(
                    "INSERT INTO items (content_hash,published_quality) VALUES (?,?)",
                    ("legacy", "reported"),
                )
                conn.commit()
                with mock.patch.object(
                    pipeline, "iso_now",
                    return_value="2026-01-01T11:00:00+00:00",
                ):
                    pipeline.process_items(conn, {"topics": [], "dedup": {}}, [])
                row = conn.execute("SELECT published_quality FROM items WHERE content_hash='legacy'").fetchone()
                self.assertEqual(row["published_quality"], "reported")
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
