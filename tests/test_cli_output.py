"""CLI privacy regression tests. All inputs are synthetic; no network."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from news_engine import cli_output
from news_engine.__main__ import main


class CliOutputTests(unittest.TestCase):
    def test_review_only_outputs_allowlisted_decision_fields(self):
        upstream = {"enabled": True, "api_key": "very-private-key", "password": "xyz",
                    "model": "Bearer leaked", "answers": {
                        "category": {"choice": "economy", "confidence": 0.7,
                                     "probabilities": {"economy": 0.7, "secret": "sensitive"},
                                     "access_token": "xyz"},
                        "text_sufficient": {"noul": 0.9, "confidence": 0.9},
                        "password": {"secret": "xyz"}}}
        result = cli_output.public_result("review", upstream)
        data = json.dumps(result)
        self.assertNotIn("very-private-key", data)
        self.assertNotIn("password", data)
        self.assertNotIn("access_token", data)
        self.assertNotIn("Bearer leaked", data)
        self.assertEqual(result["answers"]["category"]["choice"], "economy")
        self.assertEqual(result["answers"]["text_sufficient"]["noul"], 0.9)

    def test_collect_errors_are_counted_without_leaking_raw_exception(self):
        upstream = {"counts": {"total": 3, "new": 2, "errors": 1},
                    "stats": {"total": 2, "sources": []},
                    "db_path": "/home/private-user/data/news.db",
                    "errors": [{"error": "Authorization: Bearer secret-token", "source": "private"}]}
        result = cli_output.public_result("collect", upstream)
        text = json.dumps(result)
        self.assertNotIn("secret-token", text)
        self.assertNotIn("private-user", text)
        self.assertEqual(result["error_count"], 1)
        self.assertEqual(result["counts"]["new"], 2)
        self.assertEqual(result["db_path"], "news.db")

    def test_statistics_keep_public_aggregates_and_mask_obvious_secrets(self):
        result = cli_output.public_result("stats", {
            "total": 7, "topics": [{"topic": "economic_data", "c": 5}],
            "sources": [{"source": "password=abc123", "c": 7}],
            "unknown_field": "bearer private-secret"})
        self.assertEqual(result["total"], 7)
        self.assertEqual(result["topics"][0]["topic"], "economic_data")
        self.assertNotIn("abc123", json.dumps(result))
        self.assertNotIn("private-secret", json.dumps(result))

    def test_work_once_hides_error_details(self):
        result = cli_output.public_result("work-once", {
            "status": "retry_or_dead", "job_id": 4,
            "error": "Password: secret-token"})
        self.assertEqual(result, {"status": "retry_or_dead", "job_id": 4,
                                  "error": "feed_processing_failed"})

    def test_demo_cli_still_outputs_valid_json_and_counts(self):
        with tempfile.TemporaryDirectory() as path:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(main(["demo", "--data-dir", path]), 0)
            data = json.loads(stdout.getvalue())
            self.assertEqual(data["counts"]["total"], 4)
            self.assertEqual(data["note"], "Synthetic demo only. No network, no external data.")
            self.assertEqual(data["db_path"], "news.db")

    def test_review_cli_cannot_print_sensitive_sdk_fields(self):
        with tempfile.TemporaryDirectory() as path:
            cfg = Path(path) / "config.json"
            cfg.write_text(json.dumps({"gemini": {"enabled": True}}))
            # Mock the content lookup and the external call; no network or real API keys.
            fake_reply = {"enabled": True, "password": "never-log-me",
                          "answers": {"category": {"choice": "other"},
                                      "text_sufficient": {"noul": 0.1}}}
            stdout = io.StringIO()
            with mock.patch("news_engine.store.get_item", return_value={"title": "synthetic", "summary": "synthetic"}), \
                 mock.patch("news_engine.gemini_client.review", return_value=fake_reply), \
                 contextlib.redirect_stdout(stdout):
                self.assertEqual(main(["review", "--data-dir", path,
                                       "--config", str(cfg), "--item-id", "1"]), 0)
            self.assertNotIn("never-log-me", stdout.getvalue())
            self.assertEqual(json.loads(stdout.getvalue())["answers"]["category"]["choice"], "other")


if __name__ == "__main__":
    unittest.main()
