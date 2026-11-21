"""Keep the package scanner compatible with checked-out Git repositories."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.check_public_package import audit


class PackageHygieneTests(unittest.TestCase):
    def test_git_checkout_metadata_is_not_a_package_violation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / ".git" / "objects").mkdir(parents=True)
            (root / ".git" / "config").write_text("[core]\n", encoding="utf-8")
            (root / ".git" / "objects" / "test").write_text("binary\x00blob", encoding="utf-8")
            (root / "README.md").write_text("Public toolkit", encoding="utf-8")
            self.assertEqual(audit(root), [])

    def test_nested_git_metadata_is_still_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "embedded" / ".git").mkdir(parents=True)
            self.assertTrue(any("embedded" in x for x in audit(root)))

    def test_secret_and_environment_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / ".env").write_text("TOKEN=secret", encoding="utf-8")
            (root / "suspicious.txt").write_text("-----BEGIN " + "PRIVATE KEY-----", encoding="utf-8")
            findings = audit(root)
            self.assertTrue(any(".env" in x for x in findings))
            self.assertTrue(any("suspicious.txt" in x for x in findings))


if __name__ == "__main__":
    unittest.main()
