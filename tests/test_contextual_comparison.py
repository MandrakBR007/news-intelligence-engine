"""Regression contracts for selective accuracy and review-rate reporting."""
import unittest

from news_engine.contextual_comparison import compare_three
from news_engine.topic_benchmark import load_cases
from tools.compare_contextual_topics import FIXTURES, evaluate_all


class ContextualComparisonTests(unittest.TestCase):
    def test_all_frozen_datasets_are_used_without_mutation(self):
        output = evaluate_all()
        self.assertEqual(set(output), set(FIXTURES))
        self.assertEqual([output[key]["total"] for key in FIXTURES], [21, 20, 40])

    def test_all_counts_reconcile_without_accuracy_gate(self):
        for name, output in evaluate_all().items():
            with self.subTest(dataset=name):
                contextual = output["contextual"]
                total = output["total"]
                self.assertEqual(contextual["matched"] + contextual["reviewed"], total)
                self.assertEqual(sum(v["total"] for v in contextual["per_language"].values()), total)
                self.assertEqual(sum(v["matched"] for v in contextual["per_language"].values()),
                                 contextual["matched"])
                self.assertEqual(sum(v["reviewed"] for v in contextual["per_language"].values()),
                                 contextual["reviewed"])
                self.assertEqual(
                    len(contextual["false_review_vs_experimental_ids"])
                    + len(contextual["caught_experimental_errors_ids"]),
                    contextual["reviewed"],
                )
                self.assertEqual(sum(contextual["review_reasons"].values()),
                                 contextual["reviewed"])

    def test_abstention_is_not_counted_as_correct(self):
        cases = [
            {"id": "review", "language": "en",
             "title": "Film titled Monetary Policy wins award",
             "summary": "", "expected_topic": "general"},
            {"id": "match", "language": "en",
             "title": "Central bank holds interest rates",
             "summary": "", "expected_topic": "monetary_policy"},
        ]
        result = compare_three(cases)
        self.assertEqual(result["contextual"]["reviewed"], 1)
        self.assertEqual(result["contextual"]["matched"], 1)
        self.assertEqual(result["contextual"]["correct_among_matched"], 1)
        self.assertIsNone(result["cases"][0]["contextual_correct"])
        self.assertIsNone(result["cases"][0]["contextual"])

    def test_empty_input_has_null_undefined_rates(self):
        result = compare_three([])
        self.assertEqual(result["total"], 0)
        self.assertIsNone(result["contextual"]["coverage"])
        self.assertIsNone(result["contextual"]["selective_accuracy"])

    def test_deterministic_output_and_original_labels(self):
        cases = load_cases(FIXTURES["adversarial_40"])
        one = compare_three(cases)
        self.assertEqual(one, compare_three(cases))
        self.assertEqual([row["expected"] for row in one["cases"]],
                         [case["expected_topic"] for case in cases])


if __name__ == "__main__":
    unittest.main()
