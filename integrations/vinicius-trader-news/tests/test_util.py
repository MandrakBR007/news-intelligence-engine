import unittest

from news_engine import util


class UtilTests(unittest.TestCase):
    def test_content_hash_is_stable(self):
        self.assertEqual(util.content_hash("A", "B"), util.content_hash(" a ", " b "))

    def test_simhash_deterministic_and_hamming(self):
        tokens = util.tokenize("sample study on battery storage")
        a = util.simhash(tokens)
        b = util.simhash(tokens)
        self.assertEqual(a, b)
        self.assertEqual(util.hamming(a, b), 0)

    def test_jaccard(self):
        self.assertEqual(util.jaccard(["a", "b"], ["a", "b"]), 1.0)
        self.assertEqual(util.jaccard(["a"], ["b"]), 0.0)

    def test_parse_dt_iso(self):
        self.assertTrue(util.parse_dt("2026-01-01T00:00:00Z").startswith("2026-01-01T00:00:00"))
        self.assertTrue(util.parse_dt("Thu, 01 Jan 2026 09:00:00 GMT").startswith("2026-01-01T09:00:00"))


if __name__ == "__main__":
    unittest.main()
