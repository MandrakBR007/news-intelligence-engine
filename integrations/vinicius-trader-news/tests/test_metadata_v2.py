import tempfile
import unittest
from pathlib import Path

from news_engine import config, pipeline, store, util


class MetadataTests(unittest.TestCase):
    def test_missing_publication_never_becomes_current_date(self):
        self.assertIsNone(util.parse_dt(None))
        self.assertIsNone(util.parse_dt("nonsense date"))
        with tempfile.TemporaryDirectory() as d:
            cfg = config.load_config()
            item = {"source": "synthetic", "external_id": "x", "title": "Example policy bulletin",
                    "summary": "Synthetic sample", "link": "", "published_at": "invalid"}
            pipeline.run(cfg, d, feed_loader=lambda _: [item])
            c = store.connect(Path(d) / "news.db")
            store.init_db(c)
            r = store.all_items(c)[0]
            self.assertIsNone(r["published_at"])
            self.assertEqual(r["published_quality"], "missing_or_invalid")
            self.assertTrue(r["first_seen_at"])
            self.assertTrue(r["classified_at"])
            c.close()

    def test_revision_history_preserves_changes(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = config.load_config()
            record = {"source": "demo", "external_id": "same-item", "title": "Synthetic report",
                      "summary": "Original text", "link": "", "published_at": "2026-01-01T01:00:00Z"}
            pipeline.run(cfg, d, feed_loader=lambda _: [record])
            changed = dict(record, summary="Revised text")
            pipeline.run(cfg, d, feed_loader=lambda _: [changed])
            pipeline.run(cfg, d, feed_loader=lambda _: [changed])
            c = store.connect(Path(d) / "news.db")
            store.init_db(c)
            self.assertEqual(store.stats(c)["revisions"], 2)
            self.assertEqual(store.stats(c)["total"], 2)
            c.close()

    def test_etag_cache_preserves_previous_on_304(self):
        with tempfile.TemporaryDirectory() as d:
            c = store.connect(Path(d) / "x.db")
            store.init_db(c)
            store.put_cache(c, "https://example.org/feed", {"etag": '"1"', "status": 200})
            store.put_cache(c, "https://example.org/feed", {"status": 304})
            self.assertEqual(store.get_cache(c, "https://example.org/feed")["etag"], '"1"')
            c.close()


if __name__ == "__main__":
    unittest.main()
