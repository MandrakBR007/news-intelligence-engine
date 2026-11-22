"""Isolated offline contracts for explicit classifier preview (no ingestion writes)."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from news_engine import classifier_preview, classify, config, pipeline
from tools.preview_classifier_modes import main


class ClassifierPreviewTests(unittest.TestCase):
    def test_multilingual_classifies_portuguese_but_baseline_is_unchanged(self):
        article = {"title": "Boletim de inflação", "summary": ""}
        baseline = classifier_preview.preview(article, mode="baseline")
        multilingual = classifier_preview.preview(article, mode="multilingual")
        self.assertEqual(baseline["topic"], "general")
        self.assertEqual(baseline["status"], "unmatched")
        self.assertEqual(multilingual["topic"], "economic_data")
        self.assertEqual(multilingual["status"], "matched")

    def test_contextual_abstention_not_reported_as_general_decision(self):
        article = {"title": "Museu discute inflação", "summary": ""}
        output = classifier_preview.preview(article, mode="contextual")
        self.assertEqual(output["status"], "needs_review")
        self.assertIsNone(output["topic"])
        self.assertEqual(output["candidate_topic"], "economic_data")

    def test_unmatched_and_ambiguous_are_not_invented_matches(self):
        unknown = classifier_preview.preview(
            {"title": "Community garden opens"}, mode="multilingual")
        ambiguous = classifier_preview.preview(
            {"title": "Inflation and revenue"}, mode="multilingual")
        self.assertEqual(unknown["status"], "unmatched")
        self.assertEqual(ambiguous["status"], "ambiguous")
        self.assertIsNone(unknown["topic"])
        self.assertIsNone(ambiguous["topic"])

    def test_no_raw_text_or_scores_in_preview(self):
        article = {"title": "Company reports earnings SECRET_TOKEN", "summary": "PRIVATE_TEXT"}
        result = classifier_preview.preview_all(article)
        serialized = json.dumps(result)
        self.assertNotIn("SECRET_TOKEN", serialized)
        self.assertNotIn("PRIVATE_TEXT", serialized)
        self.assertNotIn("confidence", serialized)
        self.assertNotIn("matched_phrases", serialized)
        self.assertEqual(set(result["results"]), set(classifier_preview.MODES))

    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            classifier_preview.preview({"title": "Test"}, mode="production")

    def test_cli_offline_deterministic_and_does_not_print_article(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "example.json"
            path.write_text(
                json.dumps({"title": "Banco central mantém juros SECRET_TOKEN", "summary": ""}),
                encoding="utf-8",
            )
            first = io.StringIO()
            with contextlib.redirect_stdout(first), mock.patch(
                "socket.getaddrinfo", side_effect=AssertionError("network")
            ):
                self.assertEqual(main(["--input", str(path), "--mode", "all"]), 0)
            second = io.StringIO()
            with contextlib.redirect_stdout(second):
                self.assertEqual(main(["--input", str(path), "--mode", "all"]), 0)
            self.assertEqual(first.getvalue(), second.getvalue())
            self.assertNotIn("SECRET_TOKEN", first.getvalue())
            self.assertEqual(json.loads(first.getvalue())["mode"], "comparison")

    def test_existing_production_classifier_and_pipeline_not_routed(self):
        item = {"title": "Boletim de inflação", "summary": "", "external_id": "one"}
        original = classify.classify(item, config.DEFAULT_TOPICS)
        self.assertEqual(original["topic"], "general")
        with tempfile.TemporaryDirectory() as directory:
            cfg = config.load_config()
            # Preview is not hooked into the production pipeline.
            with mock.patch.object(classifier_preview, "preview",
                                   side_effect=AssertionError("preview invoked")):
                output = pipeline.run(cfg, directory, feed_loader=lambda _: [item])
            self.assertEqual(output["counts"]["new"], 1)

    def test_cli_rejects_non_object_and_oversized_files(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "example.json"
            path.write_text('"string"', encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(["--input", str(path), "--mode", "all"])
            path.write_text("x" * 65000, encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(["--input", str(path), "--mode", "baseline"])


if __name__ == "__main__":
    unittest.main()
