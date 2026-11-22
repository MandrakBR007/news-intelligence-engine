"""Experimental-only contracts; baseline ingestion behavior must not change."""
import unittest

from news_engine import classify, config, experimental_topics, topic_comparison
from news_engine.topic_benchmark import load_cases
from tools.compare_topics import HOLDOUT


class ExperimentalTopicTests(unittest.TestCase):
    def test_benchmark_baseline_result_stays_unchanged(self):
        result = topic_comparison.compare()
        self.assertEqual(result["baseline"]["correct"], 13)
        self.assertEqual(result["baseline"]["total"], 21)
        self.assertEqual(result["baseline"]["per_language"]["en"]["correct"], 9)
        self.assertEqual(result["baseline"]["per_language"]["pt-BR"]["correct"], 4)

    def test_matches_accented_portuguese_and_multiword_phrases(self):
        examples = [
            ("Boletim de inflação", "economic_data"),
            ("Produto interno bruto divulgado", "economic_data"),
            ("Banco central decide juros", "monetary_policy"),
            ("Autoridade monetária altera taxa básica", "monetary_policy"),
            ("Empresa informa receita trimestral", "business"),
            ("Retailer publishes quarterly sales", "business"),
        ]
        for title, expected in examples:
            with self.subTest(title=title):
                result = experimental_topics.classify_experimental(
                    {"title": title, "summary": ""})
                self.assertEqual(result["topic"], expected)
                self.assertEqual(result["status"], "matched")

    def test_word_boundaries_prevent_partial_keyword_matches(self):
        for title in ("Riverbank restoration", "Bankruptcy procedure", "Pricey art",
                      "General relativity lecture"):
            with self.subTest(title=title):
                result = experimental_topics.classify_experimental(
                    {"title": title, "summary": ""})
                self.assertEqual(result["topic"], "general")

    def test_unmatched_status_is_not_probability(self):
        result = experimental_topics.classify_experimental(
            {"title": "Museum exhibition opens", "summary": ""})
        self.assertEqual(result["topic"], "general")
        self.assertEqual(result["status"], "unmatched")
        self.assertEqual(result["confidence"], 0.0)

    def test_tied_topics_flag_ambiguity_instead_of_inventing_certainty(self):
        result = experimental_topics.classify_experimental(
            {"title": "Inflation and company earnings", "summary": ""})
        self.assertEqual(result["topic"], "general")
        self.assertEqual(result["status"], "ambiguous")

    def test_baseline_still_uses_unchanged_production_config(self):
        baseline = classify.classify(
            {"title": "Boletim de inflação", "summary": ""}, config.DEFAULT_TOPICS)
        self.assertEqual(baseline["topic"], "general")

    def test_new_challenge_is_separate_from_original_fixture(self):
        challenge = load_cases(HOLDOUT)
        original = load_cases()
        self.assertTrue({case["id"] for case in challenge}.isdisjoint(
            {case["id"] for case in original}))
        self.assertEqual({case["language"] for case in challenge}, {"en", "pt-BR"})
        result = topic_comparison.compare(challenge)
        self.assertEqual(result["baseline"]["total"], len(challenge))
        self.assertEqual(result["experimental"]["total"], len(challenge))
        self.assertEqual(sum(result["experimental_status_counts"].values()), len(challenge))

    def test_compare_tracks_regressions_and_recoveries(self):
        result = topic_comparison.compare()
        rows = result["cases"]
        self.assertEqual(result["recovered_case_ids"], [
            row["id"] for row in rows if not row["baseline_correct"] and
            row["experimental_correct"]])
        self.assertEqual(result["regressed_case_ids"], [
            row["id"] for row in rows if row["baseline_correct"] and
            not row["experimental_correct"]])


if __name__ == "__main__":
    unittest.main()
