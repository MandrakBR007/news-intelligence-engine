"""Synthetic tests for local, prediction-blind annotation sample export."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from news_engine import annotation_sampling, store
from tools.export_annotation_sample import main


class AnnotationSamplingTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        self.db = self.folder / "news.db"
        conn = store.connect(self.db)
        store.init_db(conn)
        rows = [
            ("h1", "cluster-1", "First article", "Secret summary 1", "policy"),
            ("h2", "cluster-1", "Reposted article", "Secret summary 2", "business"),
            ("h3", "cluster-2", "Second article", "Secret summary 3", "general"),
            ("h4", "cluster-3", "Third article", "Secret summary 4", "policy"),
        ]
        conn.executemany(
            "INSERT INTO items(content_hash,cluster_id,title,summary,topic) VALUES(?,?,?,?,?)",
            rows,
        )
        conn.commit()
        conn.close()

    def test_cluster_diverse_sample_is_deterministic(self):
        a = annotation_sampling.sample_for_annotation(self.db, limit=20, seed=17)
        b = annotation_sampling.sample_for_annotation(self.db, limit=20, seed=17)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 3)
        self.assertEqual(len({x["title"] for x in a}), 3)
        self.assertNotIn("Reposted article", [x["title"] for x in a])
        for case in a:
            self.assertEqual(case["expected_topic"], "")
            self.assertEqual(case["language"], "")
            self.assertEqual(set(case), {
                "id", "language", "title", "summary", "expected_topic",
            })
            self.assertNotIn("topic", case)

    def test_exported_file_requires_manual_labels_and_is_not_overwritten(self):
        dest = self.folder / "private_labels.json"
        output = io.StringIO()
        with contextlib.redirect_stdout(output), mock.patch(
            "socket.getaddrinfo", side_effect=AssertionError("network")
        ):
            self.assertEqual(main([
                "--db", str(self.db), "--output", str(dest),
                "--limit", "2", "--seed", "9",
            ]), 0)
        self.assertEqual(json.loads(output.getvalue())["exported"], 2)
        cases = json.loads(dest.read_text(encoding="utf-8"))
        self.assertEqual(len(cases), 2)
        self.assertIn("Secret summary", dest.read_text(encoding="utf-8"))
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(["--db", str(self.db), "--output", str(dest)])
        self.assertEqual(len(json.loads(dest.read_text(encoding="utf-8"))), 2)

    def test_source_database_is_unchanged(self):
        before = self.db.read_bytes()
        annotation_sampling.sample_for_annotation(self.db, seed=3)
        self.assertEqual(self.db.read_bytes(), before)

    def test_invalid_arguments_are_rejected(self):
        for limit, seed in ((0, 3), (201, 3), (True, 3), (3, "3")):
            with self.subTest(limit=limit, seed=seed), self.assertRaises(ValueError):
                annotation_sampling.sample_for_annotation(self.db, limit=limit, seed=seed)
        with self.assertRaises(FileNotFoundError):
            annotation_sampling.sample_for_annotation(self.folder / "missing.db")

    def test_empty_existing_db_yields_empty_private_sample(self):
        conn = store.connect(self.folder / "empty.db")
        try:
            store.init_db(conn)
        finally:
            conn.close()
        self.assertEqual(
            annotation_sampling.sample_for_annotation(self.folder / "empty.db"), []
        )

    def test_prediction_models_are_never_invoked(self):
        with mock.patch("news_engine.classify.classify", side_effect=AssertionError("classification")), \
             mock.patch("news_engine.contextual_topics.classify_contextual",
                        side_effect=AssertionError("contextual")), \
             mock.patch("news_engine.experimental_topics.classify_experimental",
                        side_effect=AssertionError("multilingual")):
            self.assertEqual(len(annotation_sampling.sample_for_annotation(self.db)), 3)


if __name__ == "__main__":
    unittest.main()
