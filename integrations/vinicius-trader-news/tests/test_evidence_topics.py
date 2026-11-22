"""Synthetic, offline regression checks for the opt-in evidence classifier."""
import json
import unittest
from unittest import mock

from news_engine.classifier_preview import preview, preview_all
from news_engine.independent_evaluation import evaluate


def case(title, expected, identifier="synthetic"):
    return {"id": identifier, "language": "en", "title": title,
            "summary": "", "expected_topic": expected}


class EvidenceTopicTests(unittest.TestCase):
    def test_positive_policy_anchor_without_generic_bank_keyword(self):
        for title in (
            "Minutes of the Federal Open Market Committee, April 1-2, 2024",
            "Federal Reserve issues FOMC statement",
            "Minutes of the Board's discount rate meetings on April 2",
            "Central bank cuts interest rates following its meeting",
        ):
            with self.subTest(title=title):
                out = preview({"title": title}, mode="evidence")
                self.assertEqual((out["status"], out["topic"]),
                                 ("matched", "monetary_policy"))

    def test_supervision_does_not_become_monetary_policy(self):
        for title in (
            "Bank supervisor announces enforcement action with former employee",
            "Board announces approval of application by Harbor Bank",
            "Agency extends comment period on proposed bank regulation",
            "Federal Reserve announces a college Fed Challenge winners event",
        ):
            with self.subTest(title=title):
                out = preview({"title": title}, mode="evidence")
                self.assertEqual((out["status"], out["topic"]), ("matched", "general"))

    def test_not_every_mention_of_bank_or_fomc_is_monetary_policy(self):
        for title in (
            "River bank restores walking trail",
            "Professor offers lecture on FOMC statement history",
            "Federal Reserve announces revised schedule of FOMC meetings in 2027",
        ):
            with self.subTest(title=title):
                out = preview({"title": title}, mode="evidence")
                self.assertNotEqual(out["topic"], "monetary_policy")

    def test_economic_and_business_anchors(self):
        cases = (
            ("Bureau releases consumer price index", "economic_data"),
            ("Institute publishes Survey of Consumer Finances", "economic_data"),
            ("Company reports earnings for second quarter", "business"),
            ("Banco central reduz juros em reuniao", "monetary_policy"),
        )
        for title, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(preview({"title": title}, mode="evidence")["topic"], expected)

    def test_unresolved_not_counted_as_correct(self):
        out = preview({"title": "Local community launches an initiative"}, mode="evidence")
        self.assertEqual(out["status"], "needs_review")
        self.assertIsNone(out["topic"])
        result = evaluate([case("Local community launches an initiative", "general")])
        engine = result["engines"]["evidence"]
        self.assertEqual((engine["correct"], engine["matched"], engine["reviews"]),
                         (0, 0, 1))

    def test_no_personal_text_or_confidence_exposure(self):
        payload = {"title": "Bank board discusses confidential matter SECRET_XYZ",
                   "summary": "PRIVATE_SUMMARY"}
        with mock.patch("socket.getaddrinfo", side_effect=AssertionError("network")):
            result = preview_all(payload)
        serialized = json.dumps(result)
        self.assertIn("evidence", result["results"])
        self.assertNotIn("SECRET_XYZ", serialized)
        self.assertNotIn("PRIVATE_SUMMARY", serialized)
        self.assertNotIn("confidence", serialized)
        self.assertNotIn("matched_phrases", serialized)

    def test_original_modes_remain_stable(self):
        data = {"title": "Inflation and revenue", "summary": ""}
        comparison = preview_all(data)["results"]
        self.assertEqual(comparison["multilingual"]["status"], "ambiguous")
        self.assertEqual(comparison["baseline"]["topic"], "economic_data")


if __name__ == "__main__":
    unittest.main()
