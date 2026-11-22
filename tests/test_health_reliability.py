"""Offline regression tests for privacy-safe diagnostics and optional AI failures."""
import contextlib
import io
import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from news_engine import cli_output, gemini_client, health, store
from news_engine.__main__ import main


class HealthReliabilityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name)
        self.conn = store.connect(self.path / "news.db")
        self.addCleanup(self.conn.close)
        store.init_db(self.conn)

    def test_health_empty_db_has_numeric_counts_without_urls(self):
        result = cli_output.public_result("health", health.diagnostic_snapshot(self.conn))
        self.assertEqual(result["items"], 0)
        self.assertEqual(result["feed_cache_entries"], 0)
        self.assertEqual(result["feeds_with_unexpected_status"], 0)
        self.assertEqual(result["queue"]["pending"], 0)
        self.assertIsNone(result["last_feed_check_at"])

    def test_health_has_only_allowlisted_fields(self):
        self.conn.execute(
            "INSERT INTO feed_cache(url,etag,last_status,checked_at) VALUES (?,?,?,?)",
            ("https://private.example.org/?token=TOP-SECRET", "TOP-SECRET", 500,
             "2026-11-22T12:00:00+00:00"),
        )
        self.conn.execute(
            "INSERT INTO feed_cache(url,etag,last_status,checked_at) VALUES (?,?,?,?)",
            ("https://other.example.org", "key", 304, "2026-11-22T13:00:00+00:00"),
        )
        self.conn.commit()
        snapshot = health.diagnostic_snapshot(self.conn)
        output = cli_output.public_result("health", snapshot)
        rendered = json.dumps(output)
        self.assertEqual(output["feed_cache_entries"], 2)
        self.assertEqual(output["feeds_with_unexpected_status"], 1)
        self.assertNotIn("TOP-SECRET", rendered)
        self.assertNotIn("private.example.org", rendered)
        self.assertNotIn("etag", rendered)
        self.assertNotIn("url", rendered)

    def test_health_cli_returns_json_without_network(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["health", "--data-dir", str(self.path)]), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["items"], 0)

    def test_ai_timeout_validation_happens_even_with_injected_client(self):
        fake = types.SimpleNamespace()
        for value in (0, 999, 120001, True, "3000"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                gemini_client.review("Title", "Summary", client=fake, timeout_ms=value)

    def test_ai_api_error_does_not_expose_tokens_or_prompt(self):
        def fail(**_kwargs):
            raise RuntimeError("Bearer PRIVATE-TOKEN Title: secret headline")
        fake = types.SimpleNamespace(decisions=types.SimpleNamespace(create=fail))
        result = gemini_client.review("secret headline", "secret summary", client=fake)
        self.assertEqual(result, {"enabled": False, "reason": "external_review_failed"})
        rendered = json.dumps(cli_output.public_result("review", result))
        self.assertNotIn("PRIVATE-TOKEN", rendered)
        self.assertNotIn("secret headline", rendered)

    def test_ai_success_contract_unchanged_with_mock(self):
        answer = types.SimpleNamespace(answers={
            "category": {"choice": "other"},
            "text_sufficient": {"noul": 0.5},
        })
        fake = types.SimpleNamespace(
            decisions=types.SimpleNamespace(create=lambda **_kw: answer))
        result = gemini_client.review("Synthetic", "Synthetic", client=fake)
        self.assertTrue(result["enabled"])
        self.assertEqual(result["answers"]["category"]["choice"], "other")

    def test_health_output_ignores_unknown_sensitive_fields(self):
        output = cli_output.public_result("health", {
            "status": "ok", "items": 1, "api_key": "PRIVATE-TOKEN",
            "last_feed_check_at": "2026-11-22", "queue": {"pending": 2, "payload": "secret"},
        })
        self.assertNotIn("PRIVATE-TOKEN", json.dumps(output))
        self.assertNotIn("payload", json.dumps(output))
        self.assertEqual(output["queue"]["pending"], 2)


if __name__ == "__main__":
    unittest.main()
