"""Regression tests for pairwise benchmark and opt-in persisted Jaccard comparison."""
import tempfile
import unittest
from pathlib import Path

from news_engine import dedup_benchmark, pipeline, store


A = {"source": "a", "external_id": "1", "title": "Synthetic harbor weather bulletin",
     "summary": "Blue winds forecast for coastal waters"}
B = {"source": "b", "external_id": "2", "title": "Coastal waters forecast for blue winds",
     "summary": "Synthetic harbor weather bulletin"}


class DedupBenchmarkTests(unittest.TestCase):
    def test_reproducible_confusion_counts(self):
        first = dedup_benchmark.evaluate()
        second = dedup_benchmark.evaluate()
        self.assertEqual(first, second)
        self.assertEqual(first["pairs"], 8)
        self.assertEqual(sum(first["counts"].values()), 8)
        self.assertIn("opposite_decision", [x["id"] for x in first["cases"]])

    def test_rejects_invalid_thresholds(self):
        with self.assertRaises(ValueError):
            dedup_benchmark.evaluate(hamming_threshold=65)
        with self.assertRaises(ValueError):
            dedup_benchmark.evaluate(jaccard_threshold=1.1)

    def test_persisted_tokens_are_opt_in(self):
        with tempfile.TemporaryDirectory() as folder:
            conn = store.connect(Path(folder) / "x.db")
            try:
                store.init_db(conn)
                cfg = {"dedup": {"hamming_threshold": -1, "jaccard_threshold": 1.0}}
                self.assertEqual(pipeline.process_items(conn, cfg, [A])["new_clusters"], 1)
                self.assertEqual(pipeline.process_items(conn, cfg, [B])["new_clusters"], 1)
            finally:
                conn.close()
        with tempfile.TemporaryDirectory() as folder:
            conn = store.connect(Path(folder) / "x.db")
            try:
                store.init_db(conn)
                cfg = {"dedup": {"hamming_threshold": -1, "jaccard_threshold": 1.0,
                                 "compare_stored_tokens": True}}
                self.assertEqual(pipeline.process_items(conn, cfg, [A])["new_clusters"], 1)
                self.assertEqual(pipeline.process_items(conn, cfg, [B])["near_duplicate"], 1)
                self.assertEqual(store.stats(conn)["clusters"], 1)
            finally:
                conn.close()

    def test_reject_non_boolean_switch(self):
        with tempfile.TemporaryDirectory() as folder:
            conn = store.connect(Path(folder) / "x.db")
            try:
                store.init_db(conn)
                with self.assertRaises(ValueError):
                    pipeline.process_items(conn, {"dedup": {"compare_stored_tokens": "false"}}, [])
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
