"""Synthetic, deterministic retry timing tests; no feeds or network calls."""
import tempfile
import unittest
from pathlib import Path

from news_engine import queue, store


class RetryBackoffTests(unittest.TestCase):
    def test_exponential_backoff_and_terminal_state(self):
        with tempfile.TemporaryDirectory() as folder:
            conn = store.connect(Path(folder) / "jobs.db")
            try:
                store.init_db(conn)
                queue.enqueue(conn, "test", {}, "backoff-case", now=100)
                first = queue.claim(conn, now=100)
                queue.fail(conn, first["id"], "temporary", max_attempts=3,
                           delay_seconds=10, backoff_factor=2, now=100)
                self.assertIsNone(queue.claim(conn, now=109))
                second = queue.claim(conn, now=110)
                self.assertEqual(second["attempts"], 2)
                queue.fail(conn, second["id"], "temporary", max_attempts=3,
                           delay_seconds=10, backoff_factor=2, now=110)
                self.assertIsNone(queue.claim(conn, now=129))
                third = queue.claim(conn, now=130)
                self.assertEqual(third["attempts"], 3)
                queue.fail(conn, third["id"], "terminal", max_attempts=3,
                           delay_seconds=10, backoff_factor=2, now=130)
                self.assertEqual(queue.stats(conn)["dead"], 1)
            finally:
                conn.close()

    def test_default_fixed_delay_remains_compatible(self):
        with tempfile.TemporaryDirectory() as folder:
            conn = store.connect(Path(folder) / "jobs.db")
            try:
                store.init_db(conn)
                queue.enqueue(conn, "test", {}, "legacy-case", now=0)
                first = queue.claim(conn, now=0)
                queue.fail(conn, first["id"], "temporary", delay_seconds=7, now=0)
                self.assertIsNone(queue.claim(conn, now=6))
                self.assertIsNotNone(queue.claim(conn, now=7))
            finally:
                conn.close()

    def test_invalid_factor_rejected_before_queue_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            conn = store.connect(Path(folder) / "jobs.db")
            try:
                store.init_db(conn)
                queue.enqueue(conn, "test", {}, "bad-factor", now=0)
                first = queue.claim(conn, now=0)
                with self.assertRaises(ValueError):
                    queue.fail(conn, first["id"], "temporary", backoff_factor=0, now=0)
                self.assertEqual(queue.stats(conn)["leased"], 1)
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
