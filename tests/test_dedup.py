import unittest

from news_engine import dedup


class DedupTests(unittest.TestCase):
    def setUp(self):
        self.a = {"title": "Sample study on battery storage",
                  "summary": "A synthetic research summary about energy storage."}
        self.b = {"title": "Sample study on battery storage",
                  "summary": "A synthetic research summary about energy storage."}
        self.c = {"title": "Open dataset for climate modeling",
                  "summary": "A synthetic announcement about climate research."}

    def test_exact_duplicate_cluster(self):
        fa = dedup.fingerprint(self.a)
        fc = dedup.fingerprint(self.c)
        existing = [{"content_hash": fa["content_hash"], "simhash": fa["simhash"],
                     "cluster_id": "cluster-a"}]
        cluster, kind = dedup.assign_cluster(fc, existing)
        self.assertEqual(kind, "new")
        cluster2, kind2 = dedup.assign_cluster(fa, existing)
        self.assertEqual(kind2, "exact")
        self.assertEqual(cluster2, "cluster-a")

    def test_near_duplicate(self):
        fa = dedup.fingerprint(self.a)
        fb = dedup.fingerprint(self.b)
        self.assertTrue(dedup.is_near(fa, fb, hamming_threshold=64))
        self.assertTrue(dedup.is_near(fa, fb, hamming_threshold=0, jaccard_threshold=0.9))

    def test_fingerprint_has_tokens(self):
        fp = dedup.fingerprint(self.a)
        self.assertIn("battery", fp["tokens"])
        self.assertIsInstance(fp["simhash"], int)


if __name__ == "__main__":
    unittest.main()
