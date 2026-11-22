import tempfile
import unittest
from pathlib import Path

from news_engine import store


def rec(**over):
    base = {
        "content_hash": "hash-1", "cluster_id": "cluster-1", "source": "demo",
        "external_id": "1", "title": "Title", "summary": "Summary", "link": "https://example.org/1",
        "published_at": "2026-01-01T00:00:00+00:00", "first_seen_at": "2026-01-01T00:00:00+00:00",
        "topic": "science", "impact": "low", "confidence": 0.1, "status": "new", "simhash": 1,
    }
    base.update(over)
    return base


class StoreTests(unittest.TestCase):
    def test_insert_and_exact_dedup(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = store.connect(Path(tmp) / "news.db")
            store.init_db(conn)
            self.assertEqual(store.insert_item(conn, rec()), 1)
            self.assertEqual(store.insert_item(conn, rec()), 0)
            self.assertEqual(store.stats(conn)["total"], 1)
            conn.close()

    def test_stats_and_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = store.connect(Path(tmp) / "news.db")
            store.init_db(conn)
            store.insert_item(conn, rec(content_hash="h1", title="A"))
            store.insert_item(conn, rec(content_hash="h2", title="B", topic="technology"))
            stats = store.stats(conn)
            self.assertEqual(stats["total"], 2)
            self.assertEqual(len(store.list_items(conn)), 2)
            conn.close()


if __name__ == "__main__":
    unittest.main()
