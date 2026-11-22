"""Offline contracts for a frozen, adversarial EN/PT topic evaluation."""
import unittest

from news_engine.topic_benchmark import LABELS, load_cases
from tools.evaluate_adversarial_topics import FIXTURE, evaluate


class AdversarialTopicEvaluationTests(unittest.TestCase):
    def test_fixture_is_frozen_and_balanced_by_language(self):
        cases = load_cases(FIXTURE)
        self.assertEqual(len(cases), 40)
        self.assertEqual(sum(case["language"] == "en" for case in cases), 20)
        self.assertEqual(sum(case["language"] == "pt-BR" for case in cases), 20)
        self.assertEqual({case["expected_topic"] for case in cases}, set(LABELS))
        self.assertEqual(len({case["id"] for case in cases}), len(cases))
        self.assertTrue(all(case["note"] for case in cases))

    def test_evaluation_deterministic_without_accuracy_threshold(self):
        first = evaluate()
        second = evaluate()
        self.assertEqual(first, second)
        self.assertEqual(first["frozen_cases"], 40)
        for version in ("baseline", "experimental"):
            summary = first[version]
            self.assertEqual(summary["total"], 40)
            self.assertEqual(summary["correct"], sum(
                row[f"{version}_correct"] for row in first["cases"]))
            self.assertEqual(sum(summary["confusion"][gold][pred]
                                 for gold in LABELS for pred in LABELS), 40)
            self.assertEqual(sum(row["cases"] for row in
                                 summary["per_language"].values()), 40)

    def test_recovered_and_regressed_cases_are_disjoint_and_auditable(self):
        report = evaluate()
        regressed = set(report["regressed_case_ids"])
        recovered = set(report["recovered_case_ids"])
        self.assertFalse(regressed & recovered)
        by_id = {row["id"]: row for row in report["cases"]}
        for case_id in regressed:
            self.assertTrue(by_id[case_id]["baseline_correct"])
            self.assertFalse(by_id[case_id]["experimental_correct"])
        for case_id in recovered:
            self.assertFalse(by_id[case_id]["baseline_correct"])
            self.assertTrue(by_id[case_id]["experimental_correct"])

    def test_challenge_groups_reconcile_with_total(self):
        report = evaluate()
        self.assertEqual(sum(row["total"] for row in
                             report["by_challenge_tag"].values()), 40)
        self.assertEqual(sum(row["experimental_correct"] for row in
                             report["by_challenge_tag"].values()),
                         report["experimental"]["correct"])

    def test_no_network_or_external_model_dependency(self):
        import socket
        from unittest import mock
        with mock.patch.object(socket, "getaddrinfo",
                               side_effect=AssertionError("network is prohibited")):
            self.assertEqual(evaluate()["frozen_cases"], 40)


if __name__ == "__main__":
    unittest.main()
