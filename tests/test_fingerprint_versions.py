"""Versioned Unicode fingerprint diagnostics; no production or network changes."""
import tempfile
import unittest
from pathlib import Path

from news_engine import dedup, fingerprint_versions, pipeline, store
from news_engine.util import tokenize

LEGACY = fingerprint_versions.LEGACY_VERSION
UNICODE = fingerprint_versions.UNICODE_VERSION


class FingerprintVersionsTests(unittest.TestCase):
    def test_unaccented_compatibility(self):
        self.assertEqual(fingerprint_versions.tokenize_unicode("Policy Rates"),
                         ["policy", "rates"])
        self.assertEqual(fingerprint_versions.tokenize_unicode("Company report 2026"),
                         ["company", "report", "2026"])

    def test_portuguese_accent_and_combining_equivalence(self):
        self.assertEqual(
            fingerprint_versions.tokenize_unicode("inflação política produção"),
            ["inflacao", "politica", "producao"],
        )
        self.assertEqual(
            fingerprint_versions.tokenize_unicode("inflação"),
            fingerprint_versions.tokenize_unicode("inflac\u0327a\u0303o"),
        )
        self.assertNotEqual(tokenize("inflação"), ["inflacao"])

    def test_legacy_fingerprint_exact_match(self):
        for item in (
            {"title": "Inflação e política monetária", "summary": "Produção cresce"},
            {"title": "Economic policy report", "summary": ""},
            {"title": "", "summary": ""},
        ):
            with self.subTest(item=item):
                fp = fingerprint_versions.fingerprint_versioned(item)
                old = dedup.fingerprint(item)
                self.assertEqual(fp["tokens"], old["tokens"])
                self.assertEqual(fp["simhash"], old["simhash"])
                self.assertEqual(fp["content_hash"], old["content_hash"])

    def test_exact_hash_stays_unchanged_across_versions(self):
        item = {"title": "Inflação 2026", "summary": "Política monetária"}
        a = fingerprint_versions.fingerprint_versioned(item, version=LEGACY)
        b = fingerprint_versions.fingerprint_versioned(item, version=UNICODE)
        self.assertEqual(a["content_hash"], b["content_hash"])
        self.assertNotEqual(a["tokens"], b["tokens"])
        self.assertNotEqual(a["simhash"], b["simhash"])

    def test_version_name_required(self):
        with self.assertRaises(ValueError):
            fingerprint_versions.fingerprint_versioned({"title": "a"}, version="v3")

    def test_comparison_is_deterministic_and_explicit(self):
        examples = [
            {"title": "Inflação", "summary": "produção"},
            {"title": "Inflation", "summary": "employment"},
        ]
        first = fingerprint_versions.compare_versions(examples)
        self.assertEqual(first, fingerprint_versions.compare_versions(examples))
        self.assertEqual(first["total"], 2)
        self.assertTrue(all(row["content_hash_unchanged"] for row in first["rows"]))
        self.assertEqual(first["token_changes"], 1)
        self.assertEqual(first["simhash_changes"], 1)

    def test_pipeline_still_persists_legacy_simhash(self):
        with tempfile.TemporaryDirectory() as directory:
            conn = store.connect(Path(directory) / "news.db")
            try:
                store.init_db(conn)
                item = {"title": "Inflação e política monetária", "summary": "Produção"}
                pipeline.process_items(conn, {"topics": [], "dedup": {}}, [item])
                stored = conn.execute("SELECT content_hash,simhash FROM items").fetchone()
                expected = dedup.fingerprint(item)
                unsigned_stored = stored["simhash"] & ((1 << 64) - 1)
                self.assertEqual(unsigned_stored, expected["simhash"])
                self.assertEqual(stored["content_hash"], expected["content_hash"])
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
