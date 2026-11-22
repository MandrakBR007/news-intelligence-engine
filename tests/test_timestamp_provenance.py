"""Deterministic timestamp provenance and revision contracts (Issue #7).

Synthetic fixtures only; no live feeds, scheduler, or schema migration.
"""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from news_engine import pipeline, store


def item(external_id, title, published=None, source="fixture"):
    return {
        "source": source,
        "external_id": external_id,
        "title": title,
        "summary": "Synthetic test description",
        "link": "https://example.org/synthetic",
        "published_at": published,
    }


class TimestampProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.conn = store.connect(Path(self.tmp.name) / "news.db")
        self.addCleanup(self.conn.close)
        store.init_db(self.conn)
        self.config = {"topics": [], "dedup": {}}

    def rows(self, table):
        # Ordering is explicit: SQLite does not guarantee implicit row order.
        return [dict(row) for row in self.conn.execute(
            f"SELECT * FROM {table} ORDER BY id ASC")]

    def test_missing_and_invalid_publication_never_use_observation_clock(self):
        records = [item("missing", "First synthetic title"),
                   item("invalid", "Second synthetic title", "nonsense")]
        clock = iter(["2026-03-01T12:00:01+00:00",
                      "2026-03-01T12:00:02+00:00",
                      "2026-03-01T12:00:03+00:00",
                      "2026-03-01T12:00:04+00:00"])
        with mock.patch.object(pipeline, "iso_now", side_effect=lambda: next(clock)):
            result = pipeline.process_items(self.conn, self.config, records)
        self.assertEqual(result["new"], 2)
        rows = self.rows("items")
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertIsNone(row["published_at"])
            self.assertEqual(row["published_quality"], "missing_or_invalid")
            self.assertEqual(row["first_seen_at"], row["ingested_at"])
            self.assertNotEqual(row["first_seen_at"], row["classified_at"])
        self.assertEqual(rows[0]["first_seen_at"], "2026-03-01T12:00:01+00:00")
        self.assertEqual(rows[0]["classified_at"], "2026-03-01T12:00:02+00:00")
        self.assertLessEqual(rows[0]["ingested_at"], rows[0]["classified_at"])
        self.assertEqual(store.stats(self.conn)["unknown_publication_time"], 2)

    def test_reported_timestamp_converts_timezone_without_substitution(self):
        with mock.patch.object(pipeline, "iso_now",
                               return_value="2026-04-03T18:00:00+00:00"):
            pipeline.process_items(self.conn, self.config, [
                item("timezone", "Third synthetic title",
                     "2026-04-03T09:45:00-03:00")])
        row = self.rows("items")[0]
        self.assertEqual(row["published_at"], "2026-04-03T12:45:00+00:00")
        self.assertEqual(row["published_quality"], "reported_tz")
        self.assertEqual(row["first_seen_at"], "2026-04-03T18:00:00+00:00")
        self.assertEqual(row["ingested_at"], row["first_seen_at"])
        self.assertEqual(store.stats(self.conn)["unknown_publication_time"], 0)

    def test_same_source_id_changed_content_creates_revision_without_rewriting_first_item(self):
        first = item("revision-id", "Original synthetic heading",
                     "2026-01-02T09:00:00+00:00")
        updated = item("revision-id", "Revised synthetic heading",
                       "2026-01-02T09:15:00+00:00")
        with mock.patch.object(pipeline, "iso_now",
                               return_value="2026-01-02T10:00:00+00:00"):
            initial = pipeline.process_items(self.conn, self.config, [first])
        first_row = self.rows("items")[0].copy()
        with mock.patch.object(pipeline, "iso_now",
                               return_value="2026-01-02T11:00:00+00:00"):
            later = pipeline.process_items(self.conn, self.config, [updated])
        rows = self.rows("items")
        revisions = self.rows("item_revisions")
        self.assertEqual(initial["new_revisions"], 1)
        self.assertEqual(later["new_revisions"], 1)
        self.assertEqual(len(revisions), 2)
        self.assertEqual([r["external_id"] for r in revisions],
                         ["revision-id", "revision-id"])
        self.assertEqual([r["observed_at"] for r in revisions],
                         ["2026-01-02T10:00:00+00:00",
                          "2026-01-02T11:00:00+00:00"])
        self.assertEqual(rows[0], first_row)
        self.assertEqual(len(rows), 2)
        self.assertEqual([r["published_at"] for r in rows],
                         ["2026-01-02T09:00:00+00:00",
                          "2026-01-02T09:15:00+00:00"])

    def test_exact_duplicate_reingestion_keeps_original_observation(self):
        original = item("same", "A synthetic duplicate headline",
                        "2026-05-01T09:00:00Z")
        with mock.patch.object(pipeline, "iso_now",
                               return_value="2026-05-01T10:00:00+00:00"):
            pipeline.process_items(self.conn, self.config, [original])
        before = self.rows("items")[0].copy()
        with mock.patch.object(pipeline, "iso_now",
                               return_value="2026-05-01T11:00:00+00:00"):
            again = pipeline.process_items(self.conn, self.config, [original])
        self.assertEqual(again["exact_duplicate"], 1)
        self.assertEqual(again["new_revisions"], 0)
        self.assertEqual(self.rows("items"), [before])
        self.assertEqual(len(self.rows("item_revisions")), 1)
        self.assertEqual(self.rows("item_revisions")[0]["observed_at"],
                         "2026-05-01T10:00:00+00:00")

    def test_content_identical_across_source_ids_has_single_item_but_two_revisions(self):
        same = item("source-A", "Shared synthetic content", source="publisher-A")
        other = item("source-B", "Shared synthetic content", source="publisher-B")
        with mock.patch.object(pipeline, "iso_now",
                               return_value="2026-06-01T10:00:00+00:00"):
            result = pipeline.process_items(self.conn, self.config, [same, other])
        self.assertEqual(result["exact_duplicate"], 1)
        self.assertEqual(result["new_revisions"], 2)
        self.assertEqual(len(self.rows("items")), 1)
        self.assertEqual(len(self.rows("item_revisions")), 2)


if __name__ == "__main__":
    unittest.main()
