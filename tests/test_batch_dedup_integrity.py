"""Offline contracts for exact-match priority and atomic SQLite batch ingestion."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from news_engine import dedup, pipeline, store


def item(number, *, title=None, summary=None):
    return {
        "source": "fixture",
        "external_id": str(number),
        "title": title or f"Synthetic headline {number}",
        "summary": summary or f"Synthetic summary {number}",
    }


class BatchDedupIntegrityTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "news.db"
        self.conn = store.connect(self.path)
        self.addCleanup(self.conn.close)
        store.init_db(self.conn)
        self.cfg = {"topics": [], "dedup": {}}

    def test_exact_match_precedes_earlier_near_match(self):
        a, b = dedup.fingerprint(item(1)), dedup.fingerprint(item(2))
        existing = [
            {"content_hash": a["content_hash"], "simhash": a["simhash"],
             "cluster_id": "near-first"},
            {"content_hash": b["content_hash"], "simhash": b["simhash"],
             "cluster_id": "exact-second"},
        ]
        expected = ("exact-second", "exact")
        self.assertEqual(dedup.assign_cluster(b, existing, 64), expected)
        self.assertEqual(dedup.assign_cluster(
            b, existing, 64,
            exact_index={row["content_hash"]: row["cluster_id"] for row in existing},
        ), expected)
        self.assertEqual(dedup.assign_cluster(
            b, existing, 64, exact_index={},
        ), ("near-first", "near"))

    def test_pipeline_global_exact_identity_when_similar_entry_comes_first(self):
        # High hamming threshold guarantees an approximate match with the first
        # entry; persisted content identity must still win on the next run.
        cfg = {"topics": [], "dedup": {"hamming_threshold": 64}}
        result = pipeline.process_items(self.conn, cfg, [item(1), item(2)])
        self.assertEqual(result["new"], 1)
        self.assertEqual(result["near_duplicate"], 1)
        repeat = pipeline.process_items(self.conn, cfg, [item(2)])
        self.assertEqual(repeat["exact_duplicate"], 1)
        self.assertEqual(repeat["near_duplicate"], 0)
        self.assertEqual(store.stats(self.conn)["total"], 2)

    def test_rollback_entire_batch_when_second_classification_fails(self):
        original = pipeline.classify_mod.classify
        calls = 0

        def fail_second(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise ValueError("synthetic classification failure")
            return original(*args, **kwargs)

        with mock.patch.object(pipeline.classify_mod, "classify", side_effect=fail_second):
            with self.assertRaisesRegex(ValueError, "synthetic"):
                pipeline.process_items(self.conn, self.cfg, [item(1), item(2)])
        self.assertEqual(store.stats(self.conn)["total"], 0)
        self.assertEqual(store.stats(self.conn)["revisions"], 0)
        # Connection remains usable after rollback.
        self.assertEqual(pipeline.process_items(self.conn, self.cfg, [item(3)])["new"], 1)

    def test_rollback_second_database_write_does_not_leave_item(self):
        with mock.patch.object(store, "add_revision", side_effect=RuntimeError("synthetic write error")):
            with self.assertRaises(RuntimeError):
                pipeline.process_items(self.conn, self.cfg, [item(1)])
        self.assertEqual(store.stats(self.conn)["total"], 0)

    def test_nested_transaction_stays_owned_by_caller(self):
        self.conn.execute("BEGIN")
        self.conn.execute(
            "INSERT INTO item_revisions(source,external_id,content_hash,observed_at) "
            "VALUES (?,?,?,?)", ("caller", "caller-id", "caller-hash", "2026-01-01")
        )
        pipeline.process_items(self.conn, self.cfg, [item(1)])
        # No hidden commit from the nested savepoint.
        self.assertTrue(self.conn.in_transaction)
        second = store.connect(self.path)
        try:
            self.assertEqual(store.stats(second)["total"], 0)
            self.assertEqual(store.stats(second)["revisions"], 0)
        finally:
            second.close()
        self.conn.rollback()
        self.assertEqual(store.stats(self.conn)["total"], 0)
        self.assertEqual(store.stats(self.conn)["revisions"], 0)

    def test_store_standalone_commit_contract_remains(self):
        record = {"content_hash": "standalone", "cluster_id": "s",
                  "source": "fixture", "external_id": "1",
                  "first_seen_at": "2026-01-01T00:00:00+00:00"}
        self.assertEqual(store.insert_item(self.conn, record), 1)
        self.assertTrue(store.add_revision(self.conn, record))
        other = store.connect(self.path)
        try:
            self.assertEqual(store.stats(other)["total"], 1)
            self.assertEqual(store.stats(other)["revisions"], 1)
        finally:
            other.close()


if __name__ == "__main__":
    unittest.main()
