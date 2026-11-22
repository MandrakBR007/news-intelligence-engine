"""Synthetic, offline contracts for optional cross-institution concept families."""
import json
import unittest
from unittest import mock

from news_engine.classifier_preview import preview, preview_all
from news_engine.independent_evaluation import evaluate


def labelled(title, category="general"):
    return {"id": "synthetic-01", "language": "en", "title": title,
            "summary": "", "expected_topic": category}


class ConceptTopicTests(unittest.TestCase):
    def test_economic_concepts_across_publication_styles(self):
        for headline in (
            "Monthly balance of payments report for the currency area",
            "International investment position at year-end",
            "New estimates of wage growth in the service sector",
            "Bank interest rate statistics released this month",
            "Quarterly monetary developments for the region",
            "Statistical office publishes gross domestic product",
            "Relatorio sobre balanca de pagamentos no trimestre",
            "Governo apresenta estatisticas de emprego",
        ):
            with self.subTest(headline=headline):
                output = preview({"title": headline}, mode="concepts")
                self.assertEqual((output["status"], output["topic"]),
                                 ("matched", "economic_data"))

    def test_policy_and_business_concepts(self):
        for title, label in (
            ("Committee discusses monetary policy transmission", "monetary_policy"),
            ("Central bank cuts rates after a vote", "monetary_policy"),
            ("Autoridade divulga decisao sobre juros", "monetary_policy"),
            ("Firm announces company merger with rival", "business"),
            ("Audited company earnings rise in quarter", "business"),
        ):
            with self.subTest(title=title):
                self.assertEqual(preview({"title": title}, mode="concepts")["topic"], label)

    def test_regulatory_and_stability_are_not_policy(self):
        for title in (
            "Bank supervision priorities unveiled",
            "Consultation on risk management guidance",
            "Report highlights financial stability risks",
            "Supervisao bancaria divulga novas regras",
        ):
            with self.subTest(title=title):
                self.assertEqual(preview({"title": title}, mode="concepts")["topic"], "general")

    def test_no_keyword_or_entity_only_shortcut(self):
        for title in (
            "Central bank launches new website",
            "Committee meeting of 12 March",
            "Interview with central banker",
            "Historical exhibit on monetary policy at museum",
        ):
            with self.subTest(title=title):
                output = preview({"title": title}, mode="concepts")
                self.assertEqual(output["status"], "needs_review")
                self.assertIsNone(output["topic"])

    def test_conflicting_signals_abstain(self):
        output = preview(
            {"title": "Monetary policy and financial stability review"},
            mode="concepts")
        self.assertEqual(output["status"], "needs_review")
        self.assertEqual(output["reason"], "conflicting_concepts")

    def test_no_raw_text_or_unvalidated_confidence_in_output(self):
        source = {"title": "A confidential gathering SECRET_SENTINEL",
                  "summary": "PRIVATE_SENTINEL"}
        with mock.patch("socket.getaddrinfo", side_effect=AssertionError("network")):
            result = preview_all(source)
        serial = json.dumps(result)
        self.assertIn("concepts", result["results"])
        self.assertNotIn("SECRET_SENTINEL", serial)
        self.assertNotIn("PRIVATE_SENTINEL", serial)
        self.assertNotIn("confidence", serial)

    def test_evaluator_accounts_for_abstention_and_frozen_engines(self):
        case = labelled("The central bank launches a website")
        evaluated = evaluate([case])["engines"]
        self.assertEqual(set(evaluated), {
            "baseline", "multilingual", "contextual", "evidence", "concepts"})
        self.assertEqual(evaluated["concepts"]["matched"], 0)
        self.assertEqual(evaluated["concepts"]["reviews"], 1)
        self.assertIsNone(evaluated["concepts"]["selective_accuracy"])
        old = preview({"title": "FOMC statement"}, mode="evidence")
        self.assertEqual(old["topic"], "monetary_policy")


if __name__ == "__main__":
    unittest.main()
