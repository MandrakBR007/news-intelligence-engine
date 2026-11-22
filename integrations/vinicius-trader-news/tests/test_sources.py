import unittest
from pathlib import Path

from news_engine.sources import parse_rss

SAMPLE = Path(__file__).resolve().parents[1] / "examples" / "sample_feed.xml"


class SourceTests(unittest.TestCase):
    def test_parse_local_synthetic_feed(self):
        items = parse_rss(SAMPLE.read_bytes(), "sample")
        self.assertEqual(len(items), 4)
        self.assertIn("inflation", items[0].title.lower())
        self.assertEqual(items[0].source, "sample")
        self.assertTrue(items[0].published_at.startswith("2026-01-01T09:00:00"))

    def test_parse_ignores_items_without_title(self):
        xml = b"<rss><channel><item><link>x</link></item></channel></rss>"
        self.assertEqual(parse_rss(xml, "sample"), [])


if __name__ == "__main__":
    unittest.main()
