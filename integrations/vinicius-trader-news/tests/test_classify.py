import unittest

from news_engine import classify, config


class ClassifyTests(unittest.TestCase):
    def test_economic_data_topic(self):
        item = {"title": "Synthetic inflation prices report", "summary": "Economic data release."}
        result = classify.classify(item, config.DEFAULT_TOPICS)
        self.assertEqual(result["topic"], "economic_data")
        self.assertIn(result["impact"], ("low", "medium", "high"))

    def test_monetary_policy_topic(self):
        item = {"title": "Central bank updates interest rates", "summary": "Policy statement."}
        result = classify.classify(item, config.DEFAULT_TOPICS)
        self.assertEqual(result["topic"], "monetary_policy")

    def test_general_topic(self):
        result = classify.classify({"title": "A neutral note", "summary": "Nothing specific."},
                                   config.DEFAULT_TOPICS)
        self.assertEqual(result["topic"], "general")
        self.assertEqual(result["confidence"], 0.0)


if __name__ == "__main__":
    unittest.main()
