"""Offline deterministic tests: per-feed cooldown and privacy-safe diagnostics."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from news_engine import cli_output, config, queue, rate_limit, store, worker


XML = b"<rss><channel><item><title>Synthetic item</title><guid>one</guid></item></channel></rss>"


def fake_fetch(url, *, etag=None, modified=None):
    return XML, {"status": 200, "etag": None, "last_modified": None}


class RateLimitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = store.connect(Path(self.tmp.name) / "test.db")
        store.init_db(self.conn)
        self.cfg = config.load_config()
        self.cfg["feeds"] = [{"name": "demo", "url": "https://example.org/feed.xml"}]
        self.cfg["queue"]["min_feed_interval_seconds"] = 60

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def test_same_feed_deferred_without_consuming_attempt(self):
        worker.enqueue_feeds(self.conn, self.cfg, batch_id="a")
        self.assertEqual(worker.work_once(self.conn, self.cfg, fetcher=fake_fetch, now=100)["status"], "done")
        worker.enqueue_feeds(self.conn, self.cfg, batch_id="b")
        second = worker.work_once(self.conn, self.cfg, fetcher=fake_fetch, now=110)
        self.assertEqual(second["status"], "deferred")
        self.assertEqual(queue.stats(self.conn)["pending"], 1)
        row = self.conn.execute("SELECT attempts,available_at FROM jobs WHERE status='pending'").fetchone()
        self.assertEqual(row["attempts"], 0)
        self.assertEqual(row["available_at"], 160)
        self.assertEqual(queue.diagnostics(self.conn, now=120)["delayed"], 1)
        self.assertEqual(worker.work_once(self.conn, self.cfg, fetcher=fake_fetch, now=159)["status"], "empty")
        self.assertEqual(worker.work_once(self.conn, self.cfg, fetcher=fake_fetch, now=160)["status"], "done")

    def test_different_feed_not_blocked(self):
        worker.enqueue_feeds(self.conn, self.cfg, batch_id="a")
        self.assertEqual(worker.work_once(self.conn, self.cfg, fetcher=fake_fetch, now=100)["status"], "done")
        self.cfg["feeds"][0]["url"] = "https://another.example.org/feed.xml"
        worker.enqueue_feeds(self.conn, self.cfg, batch_id="b")
        self.assertEqual(worker.work_once(self.conn, self.cfg, fetcher=fake_fetch, now=101)["status"], "done")

    def test_default_disabled_is_backward_compatible(self):
        self.cfg["queue"]["min_feed_interval_seconds"] = 0
        worker.enqueue_feeds(self.conn, self.cfg, batch_id="a")
        self.assertEqual(worker.work_once(self.conn, self.cfg, fetcher=fake_fetch, now=100)["status"], "done")
        worker.enqueue_feeds(self.conn, self.cfg, batch_id="b")
        self.assertEqual(worker.work_once(self.conn, self.cfg, fetcher=fake_fetch, now=101)["status"], "done")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM feed_cooldowns").fetchone()[0], 0)

    def test_rejects_malformed_config_before_claiming(self):
        self.cfg["queue"]["min_feed_interval_seconds"] = "60"
        worker.enqueue_feeds(self.conn, self.cfg, batch_id="a")
        with self.assertRaises(ValueError):
            worker.work_once(self.conn, self.cfg, fetcher=fake_fetch, now=100)
        self.assertEqual(queue.stats(self.conn)["pending"], 1)

    def test_no_source_url_in_cooldown_or_public_output(self):
        url = self.cfg["feeds"][0]["url"]
        self.assertEqual(len(rate_limit.feed_key(url)), 64)
        worker.enqueue_feeds(self.conn, self.cfg, batch_id="a")
        worker.work_once(self.conn, self.cfg, fetcher=fake_fetch, now=100)
        key = self.conn.execute("SELECT source_key FROM feed_cooldowns").fetchone()[0]
        self.assertNotIn("example.org", key)
        report = cli_output.public_result("queue-stats", queue.diagnostics(self.conn, now=110))
        self.assertIn("ready", report)
        self.assertNotIn(url, str(report))

    def test_expired_lease_and_delayed_counts(self):
        queue.enqueue(self.conn, "fetch_feed", {"feed": self.cfg["feeds"][0]}, "job", now=10)
        queue.claim(self.conn, now=10, lease_seconds=5)
        self.assertEqual(queue.diagnostics(self.conn, now=16)["expired_leases"], 1)


if __name__ == "__main__":
    unittest.main()
