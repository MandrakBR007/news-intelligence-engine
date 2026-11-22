import tempfile
import unittest
from pathlib import Path

from news_engine import queue, store


class QueueTests(unittest.TestCase):
    def test_idempotent_job_and_ack(self):
        with tempfile.TemporaryDirectory() as d:
            c = store.connect(Path(d) / "x.db")
            store.init_db(c)
            self.assertTrue(queue.enqueue(c, "test", {"value": 42}, "unique", now=100))
            self.assertFalse(queue.enqueue(c, "test", {"value": 42}, "unique", now=100))
            first = queue.claim(c, now=101, lease_seconds=30)
            self.assertEqual(first["payload"]["value"], 42)
            self.assertIsNone(queue.claim(c, now=102))
            queue.ack(c, first["id"])
            self.assertEqual(queue.stats(c)["done"], 1)
            c.close()

    def test_lease_expiry_and_terminal_failure(self):
        with tempfile.TemporaryDirectory() as d:
            c = store.connect(Path(d) / "x.db")
            store.init_db(c)
            queue.enqueue(c, "test", {}, "unique", now=100)
            j1 = queue.claim(c, now=101, lease_seconds=5)
            self.assertIsNone(queue.claim(c, now=102))
            j2 = queue.claim(c, now=107)
            self.assertEqual(j1["id"], j2["id"])
            self.assertEqual(j2["attempts"], 2)
            queue.fail(c, j2["id"], "transient", max_attempts=3, delay_seconds=4, now=108)
            self.assertIsNone(queue.claim(c, now=109))
            j3 = queue.claim(c, now=112)
            queue.fail(c, j3["id"], "permanent", max_attempts=3, now=113)
            self.assertEqual(queue.stats(c)["dead"], 1)
            c.close()


if __name__ == "__main__":
    unittest.main()
