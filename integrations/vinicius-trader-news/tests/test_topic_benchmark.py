"""Offline contracts for the generic bilingual topic benchmark (Issue #8)."""
import unittest

from news_engine import topic_benchmark


class TopicBenchmarkTests(unittest.TestCase):
    def test_fixture_is_bilingual_and_labels_are_in_scope(self):
        cases = topic_benchmark.load_cases()
        self.assertGreaterEqual(len(cases), 16)
        self.assertEqual({case["language"] for case in cases}, {"en", "pt-BR"})
        self.assertEqual({case["expected_topic"] for case in cases},
                         set(topic_benchmark.LABELS))

    def test_repeated_evaluation_is_deterministic_and_balanced(self):
        one = topic_benchmark.evaluate()
        two = topic_benchmark.evaluate()
        self.assertEqual(one, two)
        self.assertEqual(one["total"], len(one["cases"]))
        self.assertEqual(one["correct"], sum(row["correct"] for row in one["cases"]))
        self.assertEqual(sum(one["confusion"][gold][pred]
                             for gold in one["labels"] for pred in one["labels"]),
                         one["total"])
        self.assertEqual(sum(row["cases"] for row in one["per_language"].values()),
                         one["total"])

    def test_per_class_counts_derived_from_confusion(self):
        result = topic_benchmark.evaluate()
        for label in result["labels"]:
            matrix = result["confusion"]
            cls = result["per_class"][label]
            self.assertEqual(cls["support"], sum(matrix[label].values()))
            self.assertEqual(cls["tp"], matrix[label][label])
            self.assertEqual(cls["fp"], sum(matrix[gold][label] for gold in
                                            result["labels"] if gold != label))
            self.assertEqual(cls["fn"], sum(matrix[label][pred] for pred in
                                            result["labels"] if pred != label))

    def test_zero_denominators_are_explicitly_undefined(self):
        examples = [{"id": "neutral", "language": "en", "title": "Gallery opens",
                     "summary": "Public event", "expected_topic": "general"}]
        metrics = topic_benchmark.evaluate(cases=examples)
        self.assertIsNone(metrics["per_class"]["economic_data"]["precision"])
        self.assertIsNone(metrics["per_class"]["economic_data"]["recall"])
        self.assertEqual(metrics["per_class"]["general"]["precision"], 1.0)
        self.assertEqual(metrics["per_class"]["general"]["recall"], 1.0)

    def test_ambiguous_and_portuguese_cases_are_not_auto_corrected(self):
        result = topic_benchmark.evaluate()
        cases = {row["id"]: row for row in result["cases"]}
        self.assertIn("pt-economic-inflacao", cases)
        self.assertIn("en-ambiguous", cases)
        self.assertEqual(cases["pt-economic-inflacao"]["expected"], "economic_data")
        self.assertEqual(cases["en-ambiguous"]["expected"], "monetary_policy")
        self.assertIn("not a calibrated probability", result["limitations"])

    def test_invalid_fixture_rejected(self):
        with self.assertRaises(ValueError):
            topic_benchmark.evaluate(cases=[
                {"id": "bad", "language": "en", "title": "anything",
                 "summary": "", "expected_topic": "unknown_class"}
            ])


if __name__ == "__main__":
    unittest.main()
