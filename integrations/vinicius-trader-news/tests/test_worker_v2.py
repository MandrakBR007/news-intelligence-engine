import tempfile
import unittest
from pathlib import Path

from news_engine import config, queue, store, worker

XML = b"<rss><channel><item><title>Synthetic price release</title><guid>sample</guid></item></channel></rss>"


def fake_fetcher(url, *, etag=None, modified=None):
    return XML, {"status": 200, "etag": '"v1"', "last_modified": None}


class WorkerTests(unittest.TestCase):
    def test_enqueue_then_process_with_fake_feed(self):
        with tempfile.TemporaryDirectory() as d:
            c = store.connect(Path(d) / "news.db")
            store.init_db(c)
            cfg = config.load_config()
            cfg["feeds"] = [{"name": "demo", "url": "https://example.org/feed.xml"}]
            self.assertEqual(worker.enqueue_feeds(c, cfg, batch_id="round-1"), 1)
            self.assertEqual(worker.enqueue_feeds(c, cfg, batch_id="round-1"), 0)
            r = worker.work_once(c, cfg, fetcher=fake_fetcher)
            self.assertEqual(r["status"], "done")
            self.assertEqual(store.stats(c)["total"], 1)
            self.assertEqual(queue.stats(c)["done"], 1)
            self.assertEqual(worker.work_once(c, cfg)["status"], "empty")
            c.close()


if __name__ == "__main__":
    unittest.main()
