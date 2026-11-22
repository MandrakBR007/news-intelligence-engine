"""Research-only behavioral tests for conservative contextual classification."""
import unittest

from news_engine import contextual_topics


class ContextualTopicTests(unittest.TestCase):
    def test_historical_and_cultural_title_is_flagged_for_review(self):
        cases = [
            ("Historical exhibit explains inflation", "economic_data"),
            ("Museu apresenta exposição sobre inflação", "economic_data"),
            ("Film titled Monetary Policy wins award", "monetary_policy"),
            ("Juros compostos são tema de aula", "monetary_policy"),
            ("Company picnic cancelled", "business"),
        ]
        for title, candidate in cases:
            with self.subTest(title=title):
                output = contextual_topics.classify_contextual({"title": title})
                self.assertEqual(output["status"], "needs_review")
                self.assertEqual(output["reason"], "non_news_context_in_title")
                self.assertEqual(output["candidate_topic"], candidate)
                self.assertTrue(output["evidence"]["title_context_cues"])

    def test_contemporaneous_release_with_background_stays_matched(self):
        cases = [
            ("Central bank holds interest rates", "Museum exhibition offers background", "monetary_policy"),
            ("Company reports earnings after exhibition", "A museum provided context", "business"),
            ("Inflation report released", "Museum references past prices", "economic_data"),
        ]
        for title, summary, topic in cases:
            with self.subTest(title=title):
                result = contextual_topics.classify_contextual({"title": title, "summary": summary})
                self.assertEqual(result["status"], "matched")
                self.assertEqual(result["topic"], topic)

    def test_unknown_and_tie_abstain_without_inventing_topic(self):
        for title, reason in (("Community garden opens", "no_topic_evidence"),
                              ("Inflation and revenue", "topic_ambiguous")):
            with self.subTest(title=title):
                result = contextual_topics.classify_contextual({"title": title})
                self.assertEqual(result["status"], "needs_review")
                self.assertEqual(result["topic"], "general")
                self.assertIsNone(result["candidate_topic"])
                self.assertEqual(result["reason"], reason)

    def test_repeatable_and_serializable(self):
        import json
        item = {"title": "Museu discute inflação", "summary": "Bate-papo gratuito"}
        first = contextual_topics.classify_contextual(item)
        self.assertEqual(first, contextual_topics.classify_contextual(item))
        self.assertEqual(json.loads(json.dumps(first)), first)

    def test_no_network_or_ai_service(self):
        from unittest import mock
        import socket
        with mock.patch.object(socket, "getaddrinfo", side_effect=AssertionError("network")):
            self.assertEqual(contextual_topics.classify_contextual(
                {"title": "Banco central mantém juros"})["status"], "matched")


if __name__ == "__main__":
    unittest.main()
