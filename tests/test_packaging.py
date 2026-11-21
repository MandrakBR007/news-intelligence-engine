"""Check public packaging metadata and the console entry point without network calls."""
import pathlib
import tomllib
import unittest

from news_engine.__main__ import main


ROOT = pathlib.Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_metadata_and_optional_dependencies(self):
        with (ROOT / "pyproject.toml").open("rb") as f:
            config = tomllib.load(f)
        project = config["project"]
        self.assertEqual(project["name"], "news-intelligence-engine")
        self.assertEqual(project["dependencies"], [])
        self.assertEqual(project["scripts"]["news-engine"], "news_engine.__main__:main")
        self.assertIn("gemini", project["optional-dependencies"])

    def test_console_target_is_callable(self):
        self.assertTrue(callable(main))


if __name__ == "__main__":
    unittest.main()
