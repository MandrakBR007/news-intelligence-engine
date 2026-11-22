"""Synthetic offline contract tests; not a real-world performance benchmark."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from news_engine.independent_evaluation import evaluate
from tools.evaluate_labelled_news import main


CASES = [
    {"id": "a-secret", "language": "pt-BR", "title": "Boletim de inflação",
     "summary": "private_summary", "expected_topic": "economic_data"},
    {"id": "b-secret", "language": "en", "title": "Museum exhibition about inflation",
     "summary": "private_summary", "expected_topic": "general"},
    {"id": "c-secret", "language": "en", "title": "Central bank holds interest rates",
     "summary": "private_summary", "expected_topic": "monetary_policy"},
]


class IndependentEvaluationTests(unittest.TestCase):
    def test_aggregate_only_and_complete_reconciliation(self):
        result = evaluate(CASES)
        self.assertEqual(result["total"], 3)
        for engine in result["engines"].values():
            self.assertEqual(engine["total"], engine["matched"] + engine["unresolved"])
            self.assertEqual(
                engine["total"],
                engine["matched"] + engine["reviews"] +
                engine["unmatched"] + engine["ambiguous"],
            )
            self.assertEqual(sum(sum(row.values()) for row in
                                 engine["confusion_among_decided"].values()),
                             engine["matched"])
        serialized = json.dumps(result)
        for secret in ("a-secret", "b-secret", "c-secret", "private_summary",
                       "Museum exhibition"):
            self.assertNotIn(secret, serialized)

    def test_abstention_not_counted_as_correct(self):
        only_review = [dict(CASES[1], title="Museum exhibition about inflation")]
        result = evaluate(only_review)["engines"]["contextual"]
        self.assertEqual(result["reviews"], 1)
        self.assertEqual(result["matched"], 0)
        self.assertEqual(result["correct"], 0)
        self.assertIsNone(result["selective_accuracy"])
        self.assertEqual(result["correct_over_all_cases"], 0)

    def test_bad_labels_and_duplicate_ids_rejected(self):
        for cases in ([], [dict(CASES[0], expected_topic="nonexistent")],
                      [CASES[0], CASES[0]], [dict(CASES[0], language="zz")],
                      [{"title": "missing fields"}], "not a list"):
            with self.subTest(cases=cases), self.assertRaises(ValueError):
                evaluate(cases)

    def test_repeatable_output_for_identical_input(self):
        self.assertEqual(evaluate(CASES), evaluate(CASES))

    def test_cli_offline_avoids_article_text_and_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "labels.json"
            path.write_text(json.dumps(CASES), encoding="utf-8")
            out = io.StringIO()
            with mock.patch("socket.getaddrinfo", side_effect=AssertionError("network")), \
                 contextlib.redirect_stdout(out):
                self.assertEqual(main(["--input", str(path)]), 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["total"], 3)
            self.assertNotIn("private_summary", out.getvalue())
            self.assertNotIn("a-secret", out.getvalue())

    def test_cli_rejects_non_json_and_oversize(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "labels.json"
            path.write_text("{invalid", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(["--input", str(path)])
            path.write_text("x" * 2_000_001, encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(["--input", str(path)])


if __name__ == "__main__":
    unittest.main()
