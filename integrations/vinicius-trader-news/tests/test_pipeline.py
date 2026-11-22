import tempfile
import unittest
from pathlib import Path

from news_engine import config, dashboard, pipeline, store

ITEMS = [
    {"source": "demo", "external_id": "1", "title": "Sample study on battery storage",
     "summary": "Synthetic research about energy storage.", "link": "https://example.org/1",
     "published_at": "2026-01-01T09:00:00+00:00"},
    {"source": "demo", "external_id": "2", "title": "Open dataset for climate modeling",
     "summary": "Synthetic announcement about climate research.", "link": "https://example.org/2",
     "published_at": "2026-01-01T10:00:00+00:00"},
    {"source": "demo", "external_id": "3", "title": "Toolkit for reproducible text analysis",
     "summary": "Synthetic software release for digital data.", "link": "https://example.org/3",
     "published_at": "2026-01-01T11:00:00+00:00"},
    {"source": "demo", "external_id": "4", "title": "Sample study on battery storage",
     "summary": "Synthetic research about energy storage.", "link": "https://example.org/4",
     "published_at": "2026-01-01T12:00:00+00:00"},
]


class PipelineTests(unittest.TestCase):
    def test_end_to_end_synthetic_no_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = config.load_config()
            cfg["feeds"] = []
            result = pipeline.run(cfg, tmp, feed_loader=lambda _cfg: ITEMS)
            self.assertEqual(result["counts"]["total"], 4)
            self.assertEqual(result["counts"]["new"], 3)
            self.assertEqual(result["counts"]["exact_duplicate"], 1)
            self.assertTrue(Path(result["db_path"]).exists())
            conn = store.connect(result["db_path"])
            store.init_db(conn)
            self.assertEqual(store.stats(conn)["total"], 3)
            out = dashboard.build(conn, config.dashboard_path(cfg, tmp))
            self.assertTrue(out.exists())
            text = out.read_text(encoding="utf-8")
            self.assertIn("News Intelligence Engine", text)
            conn.close()


if __name__ == "__main__":
    unittest.main()
